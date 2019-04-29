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


# 测试持久连接
def test12():
    s = Session()
    s.get("http://www.httpbin.org/get")
    s.get("http://www.httpbin.org/get")

# test12()

