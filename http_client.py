import socket
import re
import dns.resolver

import requests
import urllib3


class StatusLine:
    """
    RFC2616原文：

    Status-Line = HTTP-Version SP Status-Code SP Reason-Phrase CRLF
    """

    def __init__(self, string_data):
        self.http_version = string_data.split(" ")[0]       # http版本
        self.status_code = string_data.split(" ")[1]        # 状态码
        self.reason_phrase = string_data.split(" ")[2]      # 原因短语


class Response:
    pass


# 这里用来包裹一些文本处理操作
class Utils:

    """
    这个函数是将URI解析为请求行的URI，顺便还将主机名和端口分析出来
    """
    @classmethod
    def parse_uri(cls, uri):
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


    @classmethod
    def parse_response(cls, bytes_data):

        """
        RFC2616原文：

        Response      = Status-Line       ; Section 6.1
                *(( general-header        ; Section 4.5
                 | response-header        ; Section 6.2
                 | entity-header ) CRLF)  ; Section 7.1
                CRLF
                [ message-body ]          ; Section 7.2



        """

        rtn_dict = {
            "status_line": None,
            "headers": {},
            "message_body": None
        }

        # 首先分割字节流，找到空行，即\r\n\r\n的地方，对这部分头部进行解码
        # 这里用什么字符集解码问题都不大，因为首部数据全都是ASCII字符，所以用UTF-8解码是不会出现问题的，
        # 但是报文主体就不能自己随便指定字符集了，要看头部指明的字符集来进行解码

        # 这个地方因为从服务器返回来的时候不一定按序，所以首部字段不区分类型了，除了状态行以外，其他统一称为headers

        temp = bytes_data.split(b"\r\n\r\n")[0].decode()            # 忽略报文主体，先取出首部字段

        rtn_dict["status_line"] = StatusLine(temp.split("\r\n")[0])       # 在首部信息里面，首先解析状态行

        temp = temp.split("\r\n")[1:]
        for each in temp:
            print(each.split(": "))
            rtn_dict["headers"].update({each.split(": ")[0]: each.split(": ")[1]})

        print(rtn_dict)



        return rtn_dict


a = b'HTTP/1.1 200 OK\r\nAccess-Control-Allow-Credentials: true\r\nAccess-Control-Allow-Origin: *\r\nContent-Type: application/json\r\nDate: Thu, 04 Apr 2019 12:34:15 GMT\r\nServer: nginx\r\nContent-Length: 178\r\nConnection: Close\r\n\r\n{\n  "args": {\n    "id": "1"\n  }, \n  "headers": {\n    "Host": "www.httpbin.org"\n  }, \n  "origin": "111.59.124.142, 111.59.124.142", \n  "url": "https://www.httpbin.org/get?id=1"\n}\n'

b = Utils.parse_response(a)

# print(b)
# b = a.split(b"\r\n")

# for each in b:
#    print(each)



class RequestLine:

    """
    RFC2616原文：

    Request-Line   = Method SP Request-URI SP HTTP-Version CRLF
    """

    def __init__(self, method, request_uri):
        self.method = method.upper()                                          # 请求方法，get/post/put/delete等
        self.request_uri = request_uri                                        # 请求URI
        self.http_version = "HTTP/1.1"                                      # HTTP版本 ，这里默认只使用1.1

    def to_text(self):
        return self.method + " " + self.request_uri + " " + self.http_version + "\r\n"

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

        self.__request_line = None               # 请求行
        self.__request_header = {}               # 请求首部
        self.__general_header = {}               # 通用首部
        self.__entity_header = {}                # 实体首部
        self.__extend_header = {}                # 扩展首部
        self.__body = None                       # 报文主体

        self.__infos = None                      # 这个成员变量与HTTP协议无关，方便编程而加入的变量

    def __combine_and_to_bytes(self):

        # 在这种场景下，不考虑多种MIME类型的问题同时传输和数据分块的问题。在这之后可以再针对这个东西进行优化

        data_send = ''

        # 加入起始行
        data_send += self.__request_line.to_text()

        # 遍历报文首部字典，添加报文首部
        for k, v in self.__request_header.items():
            data_send += k + ': ' + v + '\r\n'
        for k, v in self.__general_header.items():
            data_send += k + ': ' + v + '\r\n'
        for k, v in self.__entity_header.items():
            data_send += k + ': ' + v + '\r\n'
        for k, v in self.__extend_header.items():
            data_send += k + ': ' + v + '\r\n'

        # 添加空行
        data_send += '\r\n'

        # 添加主体
        if self.__body is not None:
            data_send += self.__body

        # 这里就先统一以utf-8字符集来编码，回头再讨论在首部字段中指定了实体编码的情况
        return data_send.encode('utf-8')

    def __get_info_from_uri(self, uri):
        self.__infos = Utils.parse_uri(uri)

        self.__request_header.update({"Host": self.__infos["host"], "Connection": "close"})       # 主机名加入请求头

    def __send(self, data_send):
        print(data_send)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.__infos["ip"], self.__infos["port"]))

        s.send(data_send)

        # 直接循环接收也没啥问题，但是一定要关闭持久连接。在持久连接的情况下，这个循环会堵塞，不停地接收数据
        buffer = []
        while True:
            # 每次最多接收1k字节:
            d = s.recv(1024)
            if d:
                buffer.append(d)
                print(d)
            else:
                break
        data = b''.join(buffer)


        s.close()

        return data

    def get(self, uri):
        self.__get_info_from_uri(uri)
        self.__request_line = RequestLine("get", self.__infos["request_uri"])
        response = self.__send(self.__combine_and_to_bytes())
        return response

    def post(self):
        pass

    def put(self):
        pass

    def delete(self):
        pass


# s = Request()
# resp = s.get("http://www.httpbin.org/get?id=1")
# print(resp)
