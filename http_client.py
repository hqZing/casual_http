import socket
import re
import dns.resolver


# DNS在本地缓存，不再每次都重复获取
class DNS:
    dns_dict = {}

    @classmethod
    def get_dns(cls, host_string):

        if host_string in DNS.dns_dict:
            return DNS.dns_dict[host_string]
        else:
            ip = dns.resolver.query(host_string, 'A').response.answer[-1].items[0].address
            DNS.dns_dict.update({host_string: ip})
            return ip


class RequestLine:

    """
    RFC2616原文：

    Request-Line   = Method SP Request-URI SP HTTP-Version CRLF
    """

    def __init__(self):
        self.method = "GET"                                      # 请求方法，get/post/put/delete等
        self.request_uri = "/"                                        # 请求URI
        self.http_version = "HTTP/1.1"                                      # HTTP版本 ，这里默认只使用1.1

    def build(self, method, request_uri, http_version="HTTP/1.1"):
        """
        接收参数构建请求行
        :param method:
        :param request_uri:
        :param http_version:
        :return:
        """
        self.method = method
        self.request_uri = request_uri
        self.http_version = http_version

    def parse(self, bytes_data):
        """
        从自己数据解析成请求行对象，与build作用相反
        :param bytes_data:
        :return:
        """

    def bytes(self):
        return (self.method + " " + self.request_uri + " " + self.http_version + "\r\n").encode()


class StatusLine:
    """
    RFC2616原文：

    Status-Line = HTTP-Version SP Status-Code SP Reason-Phrase CRLF
    """

    def __init__(self):
        self.http_version = ""      # http版本
        self.status_code = ""        # 状态码
        self.reason_phrase = ""      # 原因短语

    def parse(self, bytes_data):
        temp = bytes_data.decode().split(" ")
        self.http_version = temp[0]       # http版本
        self.status_code = temp[1]        # 状态码
        self.reason_phrase = temp[2]      # 原因短语


class Headers:
    def __init__(self):
        self.headers = {}

    def parse(self, bytes_data):
        self.headers = dict([x.split(": ") for x in bytes_data.decode().split("\r\n")])

    def bytes(self):
        return "".join([k + ': ' + str(v) + '\r\n' for k, v in self.headers.items()]).encode()


class Body:
    def __init__(self):
        self.__charset = "utf-8"
        self.__content_length = 0           # 消息长度，计算方法依据 RFC2616 Section 4.4，
        self.__content = ""

        # 这里把一部分实体首部给放进来比较合适，方便编程，发送报文的时候会将这里的内容更新到request对象的Headers里面
        self.__part_header = None

    def update(self):
        # 每次切换字符集之后执行一下这个，确保主体长度是正确的数值
        temp = self.__content.encode(self.__charset)
        self.__content_length = temp.__len__()
        return temp

    # 需要定义set和get方法是因为不想让用户能直接对这些属性进行操作，
    # 因为每个操作要额外执行一步update操作，直接操作属性的话会导致内容、字符集、长度不匹配
    def set_content(self, string_data):
        self.__content = string_data
        self.update()

    def set_charset(self, charset):
        self.__charset = charset
        self.update()

    def get_content(self):
        return self.__content

    def get_content_length(self):
        return self.__content_length

    def get_charset(self):
        return self.__charset

    def bytes(self):
        # 目前就不进行压缩编码了，统一用utf-8编码。得出来是多少就是多少，不进行压缩

        return self.update()


class Response:
    """
    RFC2616原文：

    Response      = Status-Line       ; Section 6.1
            *(( general-header        ; Section 4.5
             | response-header        ; Section 6.2
             | entity-header ) CRLF)  ; Section 7.1
            CRLF
            [ message-body ]          ; Section 7.2
    """

    def __init__(self):
        self.status_line = StatusLine()
        self.headers = Headers()
        self.body = Body()

    def parse_body(self, charset, bytes_data):
        self.body.set_content(bytes_data.decode(charset))

    def get_content(self):
        return self.body.get_content()


class Request:

    """
    RFC2616原文：

    Request       = Request-Line          ; Section 5.1
                *(( general-header        ; Section 4.5
                 | request-header         ; Section 5.3
                 | entity-header ) CRLF)  ; Section 7.1
                CRLF
                [ message-body ]          ; Section 4.3
    """

    def __init__(self):

        self.request_line = RequestLine()               # 请求行
        self.headers = Headers()                 # 为了与ressponse对象一致，请求首部\通用首部\实体首部\扩展首部全部混在一起了，不再单独区分
        self.body = Body()                       # 报文主体

        # 下面的变量与HTTP请求报文格式无关，是方便编程而加入的变量
        self.conn_info = {
            'port': 80,
            'request_uri': '/',
            'host': '',
            'protocol': 'HTTP/1.1',
            'ip': ''
        }

    def __parse_uri(self, uri):
        """
        这个函数是将URI解析为请求行的URI，顺便还将主机名和端口分析出来
        # 将ip，端口等信息存起来
        :param uri:
        :return:
        """

        # 这几个正则表达式应该可以合并成一个的，目前水平不够，先用判断语句来实现

        # 解析主机名
        temp = re.match("[^:]+://([^/:]+)", uri)
        self.conn_info["host"] = temp.group(1)

        # 解析端口
        temp = re.match("[^:]+://[^/:]+:([0-9]+)", uri)
        if temp is not None:
            self.conn_info["port"] = int(temp.group(1))

        # 解析request_uri
        temp = re.match("[^:]+://[^/]+/(.+)", uri)
        if temp is not None:
            self.conn_info["request_uri"] += temp.group(1)

        # 使用DNS解析域名得到ip
        self.conn_info["ip"] = DNS.get_dns(self.conn_info["host"])

    def build(self, method, uri, **kwargs):
        """
        此处根据输入的参数构建请求包
        """

        self.__parse_uri(uri)
        self.headers.headers.update({"Host": self.conn_info["host"]})       # 往请求头中加入主机名

        # get请求的参数
        u = self.conn_info["request_uri"]
        if "params" in kwargs:
            if "?" not in u:
                u += "?"
                temp = list(kwargs["params"].keys())[0]
                u += "%s=%s" % (temp, kwargs["params"][temp])
                kwargs["params"].pop(temp)

            for k, v in kwargs["params"].items():
                    u += "&%s=%s" % (k, v)

        # 构建请求行
        self.request_line.build(method.upper(), u)

        # post请求的主体数据
        if "data" in kwargs:
            temp2 = ""
            temp = list(kwargs["data"].keys())[0]
            temp2 += "%s=%s" % (temp, kwargs["data"][temp])

            kwargs["data"].pop(temp)

            for k, v in kwargs["data"].items():
                    temp2 += "&%s=%s" % (k, v)

            self.body.set_content(temp2)

            # 带上实体首部，指定实体的长度是多少，否则服务端将不能正确识别
            self.headers.headers.update({"Content-Length": self.body.get_content_length()})

            print(self.conn_info)

    def bytes(self):

        # 在这种场景下，不考虑多种MIME类型的问题同时传输和数据分块的问题。在这之后可以再针对这个东西进行优化
        rtn_bytes = b''
        rtn_bytes += self.request_line.bytes()                   # 加入起始行
        rtn_bytes += self.headers.bytes()                        # 拼接报文首部
        rtn_bytes += b'\r\n'                                         # 添加空行
        rtn_bytes += self.body.bytes()                           # 添加主体
        return rtn_bytes


class Session:
    """
    Session对象是持续不变的，而Request对象是每一次发包都重新创建的
    每一次都需要重新创建Request对象，是因为残留的变量实在太多了，一不小心可能会将上一次请求报文的内容又给继续带上去
    并且为了更贴切地表示每一次发送的请求报文都是不同的个体，每条请求报文各占用一个对象，这是比较合适的
    """
    def __init__(self):
        self.socket = None                              # 将套接字储存，用于持久连接和非持久连接
        self.store_headers = None                       # 将报文首部保存，记录客户端状态
        # self.request = Request()                      # 真正用来首发请求报文的是这个，这玩意每次都需要创建新的，用完即丢

        self.last_request = None                      # 将上一个请求包保存下来，这样，在持久连接的问题就很好处理
        self.last_response = None

    def send(self, request):
        ip, port, bytes_data = request.conn_info["ip"], request.conn_info["port"], request.bytes()
        print(ip)
        print(bytes_data)

        flag = False

        # 根据条件, 判断是否复用套接字
        if self.last_response is None:
            flag = True
        elif "close".upper() in self.last_response.headers.headers["Connection"].upper():
            flag = True
        elif ip != self.last_request.conn_info["ip"] or port != self.last_request.conn_info["port"]:
            flag = True

        if flag:
            # 直接创建新的套接字，旧的那个不关闭了，有时间再回来补全关闭套接字的代码，目前这个不影响程序
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((ip, port))

        self.socket.send(bytes_data)

        # 创建Response对象用来存储返回的这些数据
        response = Response()

        # 直接死循环接收也没啥问题，但是一定要关闭持久连接。在持久连接的情况下，这个循环会堵塞，不停地接收数据
        buffer = b''

        while True:

            d = self.socket.recv(1024)
            if d:
                buffer += d
                print(buffer)

                """
                在持久连接的情况下，接收到空行就可以先把报文首部拿过去处理了，
                先处理一下读取Content-Length才能依据这个长度来读取报文主体
                """
                if b'\r\n\r\n' in buffer:

                    temp = buffer[: buffer.find(b"\r\n")]
                    response.status_line.parse(temp)    # 解析状态行

                    temp = buffer[buffer.find(b"\r\n")+2: buffer.find(b"\r\n\r\n")]
                    response.headers.parse(temp)  # 解析响应头
                    break
            else:
                break

        # 在这里继续接收主体（如果有主体的话）
        if "Content-Length" in response.headers.headers.keys():
            print(111)
            buffer = buffer[buffer.find(b"\r\n\r\n")+4:]

            while True:

                if buffer.__len__() >= int(response.headers.headers["Content-Length"]):
                    print(222)
                    response.parse_body("utf-8", buffer)
                    break

                d = self.socket.recv(1024)
                if d:
                    buffer += d
                    print(buffer)
                else:
                    break

        print(333)
        # 持久连接搞定了！！！
        print(response.status_line.__dict__)
        print(response.headers.headers)
        print(response.get_content())
        self.last_request = request
        self.last_response = response
        return response

    def get(self, uri, **kwargs):
        request = Request()
        request.build("GET", uri)
        self.send(request)

    def post(self, uri, **kwargs):
        request = Request()
        request.build("POST", uri)
        self.send(request)

    def put(self):
        pass

    def delete(self):
        pass


s = Session()

s.get("http://www.httpbin.org/get")
# s.get("http://www.httpbin.org/get")
