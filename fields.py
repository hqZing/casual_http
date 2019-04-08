"""
这里都是一些常量，方便写代码的时候点号直接弹出，不需要开发者记忆这么多名词
我感觉还可以写得再详细一写，把
"""


# class Fields:

"""
RFC 2616 请求头域：
request-header = Accept                   ; Section 14.1
               | Accept-Charset           ; Section 14.2
               | Accept-Encoding          ; Section 14.3
               | Accept-Language          ; Section 14.4
               | Authorization            ; Section 14.8
               | Expect                   ; Section 14.20
               | From                     ; Section 14.22
               | Host                     ; Section 14.23
               | If-Match                 ; Section 14.24
               | If-Modified-Since        ; Section 14.25
               | If-None-Match            ; Section 14.26
               | If-Range                 ; Section 14.27
               | If-Unmodified-Since      ; Section 14.28
               | Max-Forwards             ; Section 14.31
               | Proxy-Authorization      ; Section 14.34
               | Range                    ; Section 14.35
               | Referer                  ; Section 14.36
               | TE                       ; Section 14.39
               | User-Agent               ; Section 14.43
"""
Accept = "Accept"
Accept_Charset = "Accept-Charset"
Accept_Encoding = "Accept-Encoding"
Accept_Language = "Accept-Language"
Authorization = "Authorization"
Expect = "Expect"
From = "From"
Host = "Host"
If_Match = "If-Match"
If_Modified_Since = "If-Modified-Since"
If_None_Match = "If-None-Match"
If_Range = "If-Range"
If_Unmodified_Since = "If-Unmodified-Since"
Max_Forwards = "Max-Forwards"
Proxy_Authorization = "Proxy-Authorization"
Range = "Range"
Referer = "Referer"
TE = "TE"
User_Agent = "User-Agent"

"""
RFC2616 响应头域：

response-header = Accept-Ranges       ; Section 14.5
            | Age                     ; Section 14.6
            | ETag                    ; Section 14.19
            | Location                ; Section 14.30
            | Proxy-Authenticate      ; Section 14.33
            | Retry-After             ; Section 14.37
            | Server                  ; Section 14.38
            | Vary                    ; Section 14.44
            | WWW-Authenticate        ; Section 14.47
"""

Accept_Ranges = "Accept-Ranges"
Age = "Age"
ETag = "ETag"
Location = "Location"
Proxy_Authenticate = "Proxy-Authenticate"
Retry_After = "Retry-After"
Server = "Server"
Vary = "Vary"
WWW_Authenticate = "WWW-Authenticate"

"""
RFC2616 实体头域
entity-header  = Allow                ; Section 14.7
           | Content-Encoding         ; Section 14.11
           | Content-Language         ; Section 14.12
           | Content-Length           ; Section 14.13
           | Content-Location         ; Section 14.14
           | Content-MD5              ; Section 14.15
           | Content-Range            ; Section 14.16
           | Content-Type             ; Se ction 14.17
           | Expires                  ; Section 14.21
           | Last-Modified            ; Section 14.29
           | extension-header
extension-header = message-header
"""

Allow = "Allow"
Content_Encoding = "Content-Encoding"
Content_Language = "Content-Language"
Content_Length = "Content-Length"
Content_Location = "Content-Location"
Content_MD5 = "Content-MD5"
Content_Range = "Content-Range"
Content_Type = "Content-Type"
Expires = "Expires"
Last_Modified = "Last-Modified"

"""
通用头域
general-header = Cache-Control        ; Section 14.9
           | Connection               ; Section 14.10
           | Date                     ; Section 14.18
           | Pragma                   ; Section 14.32
           | Trailer                  ; Section 14.40
           | Transfer-Encoding        ; Section 14.41
           | Upgrade                  ; Section 14.42
           | Via                      ; Section 14.45
           | Warning                  ; Section 14.46

"""
Cache_Control = "Cache-Control"
Connection = "Connection"
Date = "Date"
Pragma = "Pragma"
Trailer = "Trailer"
Transfer_Encoding = "Transfer-Encoding"
Upgrade = "Upgrade"
Via = "Via"
Warning = "Warning"


