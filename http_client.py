import socket
import re
import dns.resolver
import copy
from collections import UserDict
import fields as fs



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
# class PostForm:
#     # 这里应该有个便捷的方法，可以直接把抓包软件抓到的破石头
#     def parse(self, stringdata):
#         pass

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

    def build(self):
        pass

    def parse(self, bytes_data):
        self.update(dict([x.split(": ") for x in bytes_data.decode().split("\r\n")]))

    def bytes(self):
        return "".join([k + ': ' + str(v) + '\r\n' for k, v in self.items()]).encode()


class Cookies(UserDict):
    """
    chrome等浏览器的cookies存储在浏览器中。这里为了减小框架的体积，就直接放在内存里面了
    cookies的组织策略也有待考究，比如requests库的cookies是绑定在单个Session里面的，不同的会话不共享cookies
    但是浏览器的cookies是全局的，只要网站对应得上就可以取出来用
    这里沿用requests库的做法，不同会话cookies不互通
    为了加快检索速度，这里也继承字典类

    根据同源政策，两个网址只要域名和端口相同，就可以共享cookies

    """

    class cookie:
        def __init__(self, host, ip, port, time, content):
            self.host = host
            self.ip = ip
            self.port = port
            self.content = content

    """
    先使用最暴力的搜索方式，最后再构造效率更高的数据结构来替换
    """
    def __init__(self):
        UserDict.__init__(self)
        self.cookies = []

    def append(self, host, ip, port, time, content):
        self.cookies.append(cookie(host, ip, port, time, content))

    def get(self, host, ip, port):

        for i in self.cookies:
            if (i.host == host or i.ip == ip) and i.port == port:
                return i
        else:
            return None     # 如果找不到返回一个None

ck = CK()

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
            'protocol': 'HTTP/1.1',
            'ip': ''
        }

    def parse_uri(self, uri):
        """
        这个函数是将URI解析为请求行的URI，顺便还将主机名和端口分析出来
        # 将ip，端口等信息存起来
        :param uri:
        :return:
        """

        # 注意处理纯ip网址问题，不要用DNS解析纯ip的网址

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
        self.parse_uri(uri)
        print(self.conn_info)
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
        # 避免了requests库那样子还要手动改装成字典
        # 从抓包软件上面复制下来的数据就可以直接填入参数传进来了
        if "content" in kwargs:
            self.body.build(kwargs["content"])
            self.headers += self.body.part_header

        # 构建请求行
        self.request_line.build(method.upper(), u)

        # 检查本地是否有cookies， 如果有就带上
        cccc = ck.get(self.conn_info["host"], self.conn_info["ip"], self.conn_info["port"])
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
        print("recv_head......")

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
        print("recv_body......")
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

        print("send......")
        print("ip is ", ip)
        print("data to send is\t + ", bytes_data)

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
            print(response.headers["Set-Cookie"])
            ck.append(request.conn_info["host"], request.conn_info["ip"], request.conn_info["port"], None, response.headers["Set-Cookie"])
        # 检测跳转，如果有跳转，强行转化为GET方法。（这里后期要进行规则细分，不同的3xx状态码处理方式不同）
        if re.match("3..", response.status_line.status_code) is not None:
            return self.get("http://" + request.headers["Host"] + response.headers["Location"])

        return response

    def get(self, uri, **kwargs):
        request = Request()
        request.build("GET", uri, **kwargs)
        return self.proc(request)

    def post(self, uri, **kwargs):
        request = Request()
        request.build("POST", uri, **kwargs)
        self.proc(request)

    def put(self, uri, **kwargs):
        request = Request()
        request.build("PUT", uri, **kwargs)
        self.proc(request)

    def delete(self, uri, **kwargs):
        request = Request()
        request.build("DELETE", uri, **kwargs)
        self.proc(request)

    def options(self, uri, **kwargs):
        request = Request()
        request.build("OPTIONS", uri, **kwargs)
        self.proc(request)

    def head(self, uri, **kwargs):
        request = Request()
        request.build("HEAD", uri, **kwargs)
        self.proc(request)

    def connect(self):
        pass

    def trace(self):
        pass


s = Session()

hds = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36",
       "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
       "Accept-Encoding": "gzip, deflate",
       "Accept-Language": "zh-CN,zh;q=0.9",
        "Accept-Ranges": "bytes"
       }
resp = s.get("http://iw.guet.edu.cn", headers=hds)

print(resp.headers)
print(resp.body.content)
print(resp.body.content.__len__())
# s.post("http://www.httpbin.org/post", data={"a": "1", "b": "2"}, )

# s.put("http://www.httpbin.org/put", content=b"66666")

# s.delete("http://www.httpbin.org/delete")

# s.head("http://www.httpbin.org/head")

# s.options("http://www.httpbin.org/get")


# s.get("http://www.httpbin.org/redirect/3")

# 测试cookies
# s.get("http://www.yiban.cn/", headers={"Connection": "close"})
# s.get("http://www.yiban.cn/",  headers={"Connection": "close"})

# 测试断点续传
# s.get("http://down4.greenxiazai.com:8080/down/234000/201806/%E6%9A%B4%E9%A3%8E%E5%BD%B1%E9%9F%B35%20v5.76.0613.1111.rar")

a = b"123"


