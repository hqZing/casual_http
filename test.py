from http_client import *



# 测试get方法（不带参数）
def test1():
    s = Session()
    resp = s.get("http://www.httpbin.org/get")
    print(resp.body.text())
# test1()


# 测试get方法（带参数）
def test2():
    s = Session()
    resp = s.get("http://www.httpbin.org/get", params={"a": 1, "b": 2})
    print(resp.body.text())
# test2()


# 测试get方法（带参数, 带自定义请求头）
def test3():
    s = Session()
    resp = s.get("http://www.httpbin.org/get",
                 params={"a": 1, "b": 2},
                 headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 "
                                        "(KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36"})
    print(resp.body.text())
# test3()


# # 测试get方法（带参数, 带自定义请求头，请求头是字符串类型）
# def test4():
#     s = Session()
#     resp = s.get("http://www.httpbin.org/get",
#                  params={"a": 1, "b": 2},
#                  headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 "
#                                         "(KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36"})
#     print(resp.body.text())
# # test4()

# post方法，携带参数
def test5():
    s = Session()
    resp = s.post("http://www.httpbin.org/post", data={"a": "1", "b": "2"})
    print(resp.body.text())
# test5()


# put方法，携带数据
def test6():
    s = Session()
    resp = s.put("http://www.httpbin.org/put", content=b"66666")
    print(resp.body.text())
# test6()


# delete方法
def test7():
    s = Session()
    resp = s.delete("http://www.httpbin.org/delete")
    print(resp.body.text())
# test7()


# head方法
def test8():
    s = Session()
    resp = s.head("http://www.httpbin.org/get")
    print(resp.headers)
# test8()


# options方法
def test9():
    s = Session()
    resp = s.options("http://www.httpbin.org/get")
    print(resp.headers)
# test9()


# 302跳转
def test10():
    s = Session()
    resp = s.get("http://www.httpbin.org/redirect/3")
    print(resp.body.text())
# test10()


# 下载多媒体文件（这里随便从网上找个图片链接）
def test11():
    s = Session()
    resp = s.get("http://www.runoob.com/wp-content/themes/runoob/assets/img/runoob-logo.png")
    with open("runoob-logo.png", "wb") as f:
        f.write(resp.body.bytes())
# test11()


# 登陆一个网站
def test12():
    s = Session()
    resp = s.post("http://bkjw2.guet.edu.cn/student/public/login.asp",
                  data={"username": "%BB%C6%E7%F9",
                        "passwd": "10010493",
                        "login": "%B5%C7%A1%A1%C2%BC"})
    print(resp.headers)
    resp = s.get("http://bkjw2.guet.edu.cn/student/Info.asp")
    print(resp.body.bytes())
test12()

