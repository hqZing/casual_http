import socket
import re
import dns.resolver
import copy
from collections import UserDict
import fields as fs
import ssl


# 需要合并到Util里面
class Cookie:
    def __init__(self, host, port, content):
        self.host = host
        self.port = port
        self.content = content


class Util:

    # URL编码
    @classmethod
    def url_encode(cls, arg_str, safe_char="", encoding="utf-8"):
        my_map = map(lambda x: x if x in safe_char else x.encode(encoding).__str__()[2:-1].replace("\\x", "%"), arg_str)
        res_rtn = "".join(my_map)
        return res_rtn

    # DNS缓存，这个地方缓存永不过期，这么干可能会有问题，但考虑到这是个微框架，且少有网站会动不动更换解析地址，暂且这么用着
    dns_dict = {}

    @classmethod
    def get_dns(cls, host_string):

        if host_string in Util.dns_dict:
            return Util.dns_dict[host_string]
        else:
            ip = dns.resolver.query(host_string, 'A').response.answer[-1].items[0].address
            Util.dns_dict.update({host_string: ip})
            return ip

    # 本地存储cookies
    cookies = []

    @classmethod
    def append_cookies(cls, host, port, content):
        Util.cookies.append(Cookie(host, port, content))

    @classmethod
    def get_cookies(cls, host, port):

        for i in Util.cookies:
            if i.host == host and i.port == port:
                return i
        else:
            return None     # 如果找不到返回一个None


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
        注意处理中文URL问题，进行URL编码
        """
        self.method = method
        self.request_uri = request_uri
        self.http_version = http_version

    def parse(self, bytes_data):
        """
        从自己数据解析成请求行对象，与build作用相反
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
        self.reason_phrase = " ".join(temp[2:])      # 原因短语

    def build(self):
        pass


class Headers(UserDict):
    """
    message-header = field-name ":" [ field-value ]
    field-name     = token
    field-value    = *( field-content | LWS )
    field-content  = <the OCTETs making up the field-value
                     and consisting of either *TEXT or combinations
                     of token, separators, and quoted-string>

    继承字典类，对其进行功能增强, 这个类是整份代码里面用得最多、用得最方便的一个类
    """
    def __init__(self, data=None, **kwargs):
        UserDict.__init__(self)
        data = {} if data is None else data
        self.update(data)
        self.update(kwargs)

    def __add__(self, other):
        """
        重载加号运算符，实现字典相加。注意如果有相同字段，后者覆盖前者
        """
        rtn_dict = copy.deepcopy(Headers(self.data))
        rtn_dict.update(other)
        return rtn_dict

    def build(self, data):

        # 如果传进来的是个字典，那么就直接加进去，如果是普通字符串，就解析做成字典
        if isinstance(data, str):
            pass
        if isinstance(data, dict):
            self.update(data)

    def parse(self, bytes_data):
        self.update(dict([x.split(": ") for x in bytes_data.decode().split("\r\n")]))

    def bytes(self):
        return "".join([k + ': ' + str(v) + '\r\n' for k, v in self.items()]).encode()


class Body:

    """
    这里是整份代码之中的唯一一个特殊情况，此处content是存储字节流的，其他类都是直接存储字符串的
    这里存储字节流是因为下载二进制文件的时候无法以字符串保存内容
    """
    def __init__(self):
        self.charset = "utf-8"
        self.content = b""

        # 这里把一部分实体首部给放进来比较合适，方便编程，发送报文的时候会将这里的内容更新到request对象的Headers里面
        # 消息长度，计算方法依据 RFC2616 Section 4.4，
        self.part_header = Headers() + {"Content-Length": 0}

    def build(self, string_or_bytes_data, charset="utf-8", **kwargs):
        """
        这里既可以接收字符串，也可以接收字节流

        """
        data = string_or_bytes_data

        # 如果是字节类型就直接存储
        if isinstance(data, bytes):
            self.content = data

        # 如果是字符串就编码成字节数组再存储
        if isinstance(data, str):
            self.charset = charset
            self.content = data.encode(self.charset)

        # 存储之后记录下长度
        self.part_header["Content-Length"] = self.content.__len__()

        if "content_type" in kwargs:
            self.part_header["Content-Type"] = kwargs["content_type"]

    def parse(self, bytes_data, charset="utf-8"):
        """
        因为类型的特殊性，这里parse和build实际上已经是同一个函数了，保留这个为了语义方便理解
        """
        self.build(bytes_data, charset)

    def bytes(self):
        return self.content

    def text(self):
        return self.content.decode(self.charset)


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
            'version': '1.1',
            'ip': '',
            "protocol": "http"
        }

    def parse_uri(self, uri):
        """
        这个函数是将URI解析为请求行的URI，顺便还将主机名和端口分析出来
        将ip，端口等信息存起来
        业界有不成文规定，（大多数）浏览器通常都会限制url长度在2K个字节，而（大多数）服务器最多处理64K大小的url。

        """
        uri_pattern = "((\w+):\/\/)?([^/:]+)(:\d*)?([^# ]*)"
        uri_match = re.match(uri_pattern, uri)

        if uri_match is None:
            raise Exception("URI不合法!")

        self.conn_info["protocol"] = uri_match.group(2)                  # 解析协议
        self.conn_info["host"] = uri_match.group(3)                        # 解析主机名
        self.conn_info["request_uri"] = uri_match.group(5)              # 解析请求uri
        self.conn_info["port"] = uri_match.group(4)                      # 解析端口

        # 默认协议http
        if self.conn_info["protocol"] is None:
            self.conn_info["protocol"] = "http"

        # 默认端口80/443
        if self.conn_info["port"] is None:
            self.conn_info["port"] = 443 if self.conn_info["protocol"] == "https" else 80
        else:
            self.conn_info["port"] = self.conn_info["port"][1:]

        # 请求URL后面补全斜杠，并处理URL编码
        if self.conn_info["request_uri"] == "":
            self.conn_info["request_uri"] = "/"
        self.conn_info["request_uri"] = Util.url_encode(self.conn_info["request_uri"], ";/?:@&=+$,", "utf-8")

        # 使用DNS解析域名得到ip，注意处理纯ip网址问题，不要用DNS解析纯ip的网址
        if re.match("[.\d]+", self.conn_info["host"]) is None:
            self.conn_info["ip"] = Util.get_dns(self.conn_info["host"])
        else:
            self.conn_info["ip"] = self.conn_info["host"]

        print(self.conn_info)

    def build(self, method, uri, **kwargs):
        """
        此处根据输入的参数构建请求包
        """
        self.parse_uri(uri)
        # print(self.conn_info)
        self.headers += {"Host": self.conn_info["host"]}       # 往请求头中加入主机名

        # 处理额外传入的自定义header
        if kwargs.__contains__("headers"):
            self.headers += kwargs["headers"]

        # get请求的参数
        u = self.conn_info["request_uri"]
        if "params" in kwargs:
            u += "?" if "?" not in u else "&"
            u += "&".join(["%s=%s" % (k, v) for k, v in kwargs["params"].items()])

        # post请求的参数
        if "data" in kwargs:
            temp = "&".join(["%s=%s" % (k, v) for k, v in kwargs["data"].items()])
            self.body.build(temp)
            self.headers += self.body.part_header   # 带上首部，指定实体的长度是多少，否则服务端将不能正确识别

        # content这个字段，不只是put请求会用到，post请求也可以通过设置这个东西来传输原始数据
        # 这里可以接收字符串或者字典，直接输入原始数据放到报文主体里面也是可以的，不必要像requests那样一定封装成字典
        if "content" in kwargs:
            self.body.build(kwargs["content"])
            self.headers += self.body.part_header

        # 构建请求行
        self.request_line.build(method.upper(), u)

        # 检查本地是否有cookies， 如果有就带上
        cccc = Util.get_cookies(self.conn_info["host"], self.conn_info["port"])
        # print(cccc)
        # print(ck.cookies.__str__())
        if cccc is not None:
            self.headers += {"Cookies": cccc.content}

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
        self.cookies = None                       # 将cookies保存，记录客户端状态
        # self.request = Request()                      # 真正用来首发请求报文的是这个，这玩意每次都需要创建新的，用完即丢

        self.last_request = None                      # 将上一个请求包保存下来，这样，在持久连接的问题就很好处理
        self.last_response = None

    def recv_head(self, response, buffer, **kwargs):
        print("接受响应头......")

        while True:

            d = self.socket.recv(1024)
            if d:
                buffer += d
                print(buffer)
                if b'\r\n\r\n' in buffer:
                    response.status_line.parse(buffer[: buffer.find(b"\r\n")])    # 解析状态行
                    response.headers.parse(buffer[buffer.find(b"\r\n")+2: buffer.find(b"\r\n\r\n")])  # 解析响应头
                    break
            else:
                break       # 如果服务端已经断开连接，那就没必要再继续接收了

        # 把报文首部截去
        buffer = buffer[buffer.find(b"\r\n\r\n") + 4:]
        return buffer

    def recv_body(self, response, buffer):
        print("接收响应主体......")
        while True:
            if buffer.__len__() >= int(response.headers["Content-Length"]):
                response.body.parse(buffer)
                break
            d = self.socket.recv(1024)
            if d:
                buffer += d
            else:
                break
        return buffer

    def send(self, request):

        ip, port, bytes_data = request.conn_info["ip"], request.conn_info["port"], request.bytes()

        print("准备发送请求报文......")
        print("发往的ip是......", ip)
        print("发送的字节流是\t", bytes_data)

        flag = False

        # 根据条件, 判断是否复用套接字
        if self.last_response is None:
            flag = True
        elif "close".upper() in self.last_response.headers["Connection"].upper():
            flag = True
        elif ip != self.last_request.conn_info["ip"] or port != self.last_request.conn_info["port"]:
            flag = True

        if flag:
            # 直接创建新的套接字，旧的那个不关闭了，有时间再回来补全关闭套接字的代码，目前这个不影响程序

            # 如果是https
            if request.conn_info["protocol"] == "https":

                context = ssl.create_default_context()
                self.socket = context.wrap_socket(socket.socket(socket.AF_INET),
                                                  server_hostname=request.conn_info["host"])
                self.socket.connect((ip, port))
            # 如果是http
            else:
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.connect((ip, port))

        self.socket.send(bytes_data)

    def proc(self, request):
        """
        应该在这里调用send和recv函数，发送和接收就只管发送接收，处理业务逻辑应该就在这里完成
        包括重定向跳转和储存cookies的过程应该最好也就在这里处理
        :return:
        """
        # print("proc......")
        self.send(request)

        # 创建Response对象用来存储返回的这些数据
        response = Response()
        buffer = b""

        # 接收响应报文头
        buffer = self.recv_head(response, buffer)

        if "Content-Length" in response.headers.keys() and request.request_line.method != "HEAD":
            # 在这里继续接收主体（如果有主体的话）
            self.recv_body(response, buffer)

        # print("proc done......")
        # print(response.status_line.__dict__)
        # print(response.headers)
        # print(response.body.bytes())

        self.last_response = response
        self.last_request = request

        # 检测set-cookies
        if response.headers.__contains__("Set-Cookie"):
            pass
            # print(response.headers["Set-Cookie"])
            ck.append(request.conn_info["host"], request.conn_info["port"], response.headers["Set-Cookie"])
        # 检测跳转，如果有跳转，强行转化为GET方法。（这里后期要进行规则细分，不同的3xx状态码处理方式不同）
        if re.match("3..", response.status_line.status_code) is not None:
            if response.headers["Location"][0] != "/":
                response.headers["Location"] = "/" + response.headers["Location"]
            return self.get("http://" + request.headers["Host"] + response.headers["Location"])

        return response

    def get(self, uri, **kwargs):
        request = Request()
        request.build("GET", uri, **kwargs)
        return self.proc(request)

    def post(self, uri, **kwargs):
        request = Request()
        request.build("POST", uri, **kwargs)
        return self.proc(request)

    def put(self, uri, **kwargs):
        request = Request()
        request.build("PUT", uri, **kwargs)
        return self.proc(request)

    def delete(self, uri, **kwargs):
        request = Request()
        request.build("DELETE", uri, **kwargs)
        return self.proc(request)

    def options(self, uri, **kwargs):
        request = Request()
        request.build("OPTIONS", uri, **kwargs)
        return self.proc(request)

    def head(self, uri, **kwargs):
        request = Request()
        request.build("HEAD", uri, **kwargs)
        return self.proc(request)

    def connect(self):
        pass

    def trace(self):
        pass


s = Session()
resp = s.get("http://www.httpbin.org/get?a=啊啊啊")
print(resp.body.text())

