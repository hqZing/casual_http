import socket
import re
import dns.resolver


class RequestLine:

    """
    RFC2616原文：

    Request-Line   = Method SP Request-URI SP HTTP-Version CRLF
    """

    def __init__(self):
        self.__method = "GET"                                      # 请求方法，get/post/put/delete等
        self.__request_uri = "/"                                        # 请求URI
        self.__http_version = "HTTP/1.1"                                      # HTTP版本 ，这里默认只使用1.1

    def get_method(self):
        return self.__method

    def get_request_uri(self):
        return self.__request_uri

    def get_http_version(self):
        return self.__http_version

    def set_method(self, method):
        self.__method = method

    def set_request_uri(self, request_uri):
        self.__request_uri = request_uri

    def set_http_version(self, http_version):
        self.__http_version = http_version

    def get_byte(self):
        return (self.__method + " " + self.__request_uri + " " + self.__http_version + "\r\n").encode()



class StatusLine:
    """
    RFC2616原文：

    Status-Line = HTTP-Version SP Status-Code SP Reason-Phrase CRLF
    """

    def __init__(self):
        self.http_version = ""      # http版本
        self.status_code = ""        # 状态码
        self.reason_phrase = ""      # 原因短语

    def parse(self, string_data):
        self.http_version = string_data.split(" ")[0]       # http版本
        self.status_code = string_data.split(" ")[1]        # 状态码
        self.reason_phrase = string_data.split(" ")[2]      # 原因短语


class Headers:
    def __init__(self):
        self.__headers = {}

    def set_headers(self, headers):
        self.__headers.update(headers)

    def get_headers(self):
        return self.__headers

    def get_byte(self):
        rtn_text = ""
        for k, v in self.__headers.items():
            rtn_text += k + ': ' + str(v) + '\r\n'
        return rtn_text.encode()


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

    def get_byte(self):
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
        self.__status_line = StatusLine()
        self.__headers = Headers()
        self.__body = Body()

    def parse_head(self, bytes_data):

        # 首先分割字节流，找到空行，即\r\n\r\n的地方，对这部分头部进行解码
        # 这里用什么字符集解码问题都不大，因为首部数据全都是ASCII字符，所以用UTF-8解码是不会出现问题的，
        # 但是报文主体就不能自己随便指定字符集了，要看头部指明的字符集来进行解码

        # 这个地方因为从服务器返回来的时候不一定按序，所以首部字段不区分类型了，除了状态行以外，其他统一称为headers

        temp = bytes_data.split(b"\r\n\r\n")[0].decode()            # 忽略报文主体，先取出首部字段

        self.__status_line.parse(temp.split("\r\n")[0])      # 在首部信息里面，首先解析状态行

        temp = temp.split("\r\n")[1:]
        for each in temp:
            self.__headers.set_headers({each.split(": ")[0]: each.split(": ")[1]})

        print(self.__headers.get_headers())

    def parse_body(self, charset, bytes_data):
        self.__body.set_content(bytes_data.decode(charset))

    def get_headers(self):
        return self.__headers.get_headers()

    def set_headers(self, dict_data):
        self.__headers.set_headers(dict_data)

    def get_content(self):
        return self.__body.get_content()






# a = b'HTTP/1.1 200 OK\r\nAccess-Control-Allow-Credentials: true\r\nAccess-Control-Allow-Origin: *\r\nContent-Type: application/json\r\nDate: Thu, 04 Apr 2019 12:34:15 GMT\r\nServer: nginx\r\nContent-Length: 178\r\nConnection: Close\r\n\r\n{\n  "args": {\n    "id": "1"\n  }, \n  "headers": {\n    "Host": "www.httpbin.org"\n  }, \n  "origin": "111.59.124.142, 111.59.124.142", \n  "url": "https://www.httpbin.org/get?id=1"\n}\n'

# b = Utils.parse_response(a)

# print(b)
# b = a.split(b"\r\n")

# for each in b:
#    print(each)





#
# r = RequestLine("get", "http://www.baidu.com/get")
# print(r.to_text())



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

        self.__request_line = RequestLine()               # 请求行
        self.__headers = Headers()                 # 为了与ressponse对象一致，请求首部\通用首部\实体首部\扩展首部全部混在一起了，不再单独区分
        self.__body = Body()                       # 报文主体

        # 下面的变量与HTTP请求报文格式无关，是方便编程而加入的变量
        self.__infos = None

    """
    这个函数是将URI解析为请求行的URI，顺便还将主机名和端口分析出来
    """
    def parse_uri(self, uri, **kwargs):
        rtn_dict = {
            'port': 80,
            'request_uri': '/',
            'host': '',
            'protocal': 'HTTP/1.1',
            'ip': ''
        }

        # 这几个正则表达式应该可以合并成一个的，目前水平不够，先用判断语句来实现

        # 解析主机名
        temp = re.match("[^:]+://([^/:]+)", uri)
        rtn_dict["host"] = temp.group(1)

        # 解析端口
        temp = re.match("[^:]+://[^/:]+:([0-9]+)", uri)
        if temp is not None:
            rtn_dict["port"] = temp.group(1)

        # 解析request_uri
        temp = re.match("[^:]+://[^/]+/(.+)", uri)
        if temp is not None:
            rtn_dict["request_uri"] += temp.group(1)

        # 使用DNS解析域名得到ip
        rtn_dict["ip"] = dns.resolver.query(rtn_dict["host"], 'A').response.answer[-1].items[0].address

        print(rtn_dict)
        return rtn_dict



    def __create(self, uri, **kwargs):

        self.__infos = self.parse_uri(uri)
        self.__headers.set_headers({"Host": self.__infos["host"], "Connection": "close"})       # 主机名加入请求头
        self.__request_line.set_request_uri(self.__infos["request_uri"])

        # 请求方法
        if "method" in kwargs:
            self.__request_line.set_method(kwargs["method"].upper())

        # get请求的时候可以自动加入这些参数
        if "params" in kwargs:
            u = self.__request_line.get_request_uri()
            if "?" not in u:
                u += "?"
                temp = list(kwargs["params"].keys())[0]
                u += "%s=%s" % (temp, kwargs["params"][temp])
                kwargs["params"].pop(temp)

            for k, v in kwargs["params"].items():
                    u += "&%s=%s" % (k, v)
            self.__request_line.set_request_uri(u)

        # post请求的时候会将这些东西加入报文主体
        if "data" in kwargs:
            temp2 = ""
            temp = list(kwargs["data"].keys())[0]
            temp2 += "%s=%s" % (temp, kwargs["data"][temp])

            kwargs["data"].pop(temp)

            for k, v in kwargs["data"].items():
                    temp2 += "&%s=%s" % (k, v)

            self.__body.set_content(temp2)

            # 带上实体首部，指定实体的长度是多少，否则服务端将不能正确识别
            self.__headers.set_headers({"Content-Length": self.__body.get_content_length()})

    def __combine(self):

        # 在这种场景下，不考虑多种MIME类型的问题同时传输和数据分块的问题。在这之后可以再针对这个东西进行优化
        data_send = b''
        data_send += self.__request_line.get_byte()                 # 加入起始行
        data_send += self.__headers.get_byte()              # 拼接报文首部
        data_send += b'\r\n'                                 # 添加空行
        data_send += self.__body.get_byte()                 # 添加主体

        return data_send

    def __send(self, data_send):
        print(data_send)
        so = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        so.connect((self.__infos["ip"], self.__infos["port"]))

        so.send(data_send)

        # 直接死循环接收也没啥问题，但是一定要关闭持久连接。在持久连接的情况下，这个循环会堵塞，不停地接收数据
        buffer = []
        while True:
            # 每次最多接收1k字节:
            d = so.recv(1024)
            if d:
                buffer.append(d)
                print(d)
            else:
                break
        data = b''.join(buffer)

        so.close()

        return data

    def get(self, uri, **kwargs):
        if "parmas" in kwargs:
            self.__create(uri, method="get", params=kwargs["parmas"])
        else:
            self.__create(uri, method="get")
        response = self.__send(self.__combine())
        return response

    def post(self, uri, **kwargs):
        """
        在post这里需要注意的地方就是，因为post请求是有body的，需要获取一次body的字节长度加入请求头
        """
        if "data" in kwargs:
            self.__create(uri, method="post", data=kwargs["data"])
        else:
            self.__create(uri, method="post")

        response = self.__send(self.__combine())
        return response

    def put(self):
        pass

    def delete(self):
        pass


# s = Request()
# resp = s.post("http://www.httpbin.org/post", data={"b": 1})
# print(resp)


class Session:
    """
    Session对象是持续不变的，而Request对象是每一次发包都重新创建的
    每一次都需要重新创建Request对象，是因为残留的变量实在太多了，一不小心可能会将上一次请求报文的内容又给继续带上去
    并且为了更贴切地表示每一次发送的请求报文都是不同的个体，每条请求报文各占用一个对象，这是比较合适的
    """
    def __init__(self):
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)       # 将套接字储存，用于持久连接和非持久连接
        self.__headers = None                   # 将报文首部保存，记录客户端状态
        self.__request = Request()                      # 真正用来首发请求报文的是这个，这玩意每次都需要创建新的，用完即丢

        self.__keep_alive = True                        # 持久连接默认都是开启的

    def send(self, ip, port, bytes_data):

        # 创建Response对象用来存储返回的这些数据
        response = Response()

        self.__socket.connect((ip, port))
        self.__socket.send(bytes_data)

        # 直接死循环接收也没啥问题，但是一定要关闭持久连接。在持久连接的情况下，这个循环会堵塞，不停地接收数据
        buffer = b''

        while True:

            d = self.__socket.recv(1024)
            if d:
                buffer += d
                print(buffer)

                """
                在持久连接的情况下，接收到空行就可以先把报文首部拿过去处理了，
                先处理一下读取Content-Length才能依据这个长度来读取报文主体
                """
                if b'\r\n\r\n' in buffer:
                    response.parse_head(buffer)     # 解析响应头
                    break
            else:
                break

        if "Connection" in response.get_headers().keys():
            if "close" in response.get_headers()["Connection"]:
                self.__keep_alive = False
            if "Keep-Alive" in response.get_headers()["Connection"]:
                self.__keep_alive = True

        # 在这里继续接收主体（如果有主体的话）
        if "Content-Length" in response.get_headers().keys():
            print(111)
            buffer = buffer.split(b"\r\n\r\n")[1]

            while True:

                if buffer.__len__() >= int(response.get_headers()["Content-Length"]):
                    print(222)
                    response.parse_body("utf-8", buffer)
                    break

                d = self.__socket.recv(1024)
                if d:
                    buffer += d
                    print(buffer)
                else:
                    break

        if not self.__keep_alive:
            self.__socket.close()
        print(333)
        # 持久连接搞定了！！！
        print(response.get_headers())
        print(response.get_content())
        return response


s = Session()
ddd = b'POST /post HTTP/1.1\r\nHost: www.httpbin.org\r\nContent-Length: 3\r\n\r\nb=1'
s.send("3.85.154.144", 80, ddd)

