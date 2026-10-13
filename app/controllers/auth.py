"""
认证有关的Controller:登录、注册、登出
LoginHandler: 登录 GET:展示登录页面, POST:处理登录请求并写登录cookie
RegisterHandler: 注册 GET:展示注册页面, POST:处理注册请求并创建用户
LogoutHandler: 登出 POST:处理登出请求并清除登录cookie

这些接口与传统表单提交一致, 成功用redirect跳转
失败则重新渲染对应页面, 并通过error变量回显错误信息
XSRF token 由模板中的{% module "xsrf_form_html()" %}自动随表单提交, Tornado会自动验证
"""
from app.controllers.base import BaseHandler
from app.models.user import UserRepository

class LoginHandler(BaseHandler):
    def get(self):
        """展示登录页面"""
        self.render("login.html", title="登录", error=None)

    def post(self):
        """处理登录请求并写登录cookie"""
        username = self.get_body_argument("username", "")
        password = self.get_body_argument("password", "")

        if not username or not password:
            self.set_status(400)
            self.render("login.html", title="登录", error="用户名和密码不能为空")
            return
        
        if not UserRepository.verify_user(username, password):
            self.set_status(401)
            self.render("login.html", title="登录", error="用户名或密码错误")
            return

        self.set_secure_cookie("username", username)
        self.redirect(self.get_argument("next", "/"))  # 登录成功后跳转到next参数指定的页面，若未指定则跳转到首页

class RegisterHandler(BaseHandler):
    def get(self):
        """展示注册页面"""
        self.render("register.html", title="注册", error=None)

    def post(self):
        """处理注册请求并创建用户"""
        username = self.get_body_argument("username","")
        password = self.get_body_argument("password","")
        password2 = self.get_body_argument("password2","")

        if not username or not password or not password2:
            self.set_status(400)
            self.render("register.html", title="注册", error="所有字段都不能为空")
            return

        if password != password2:
            self.set_status(400)
            self.render("register.html", title="注册", error="两次输入的密码不一致")
            return

        if not UserRepository.create_user(username, password):
            self.set_status(409)
            self.render("register.html", title="注册", error="用户名已存在")
            return

        self.redirect("/auth/login")  # 注册成功后跳转到登录页面
        
class LogoutHandler(BaseHandler):
    def post(self):
        """处理登出请求并清除登录cookie"""
        self.clear_cookie("username")
        self.redirect("/auth/login")  # 登出后跳转到登录页面