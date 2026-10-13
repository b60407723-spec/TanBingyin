"""
测试用例：
通过代码脚本运行测试用例：用户登录和用户注册功能的测试
测试方法：
python test/test_user.py
"""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))

from app.models.db import get_connection, init_db
from app.models.user import UserRepository

USERNAME = "testuser"
PASSWORD = "testpassword"

init_db()  # 初始化数据库及表
with get_connection() as conn:
    # 清空users表
    conn.execute("delete from users where username = ?", (USERNAME,))

UserRepository.create_user(USERNAME, PASSWORD)

assert UserRepository.verify_user(USERNAME, PASSWORD) is True, "正确密码登录成功"
assert UserRepository.verify_user(USERNAME, "wrongpassword") is False, "错误密码登录失败"
assert UserRepository.verify_user("wronguser", PASSWORD) is False, "错误用户名登录失败"

with get_connection() as conn:
    # 清空users表
    conn.execute("delete from users where username = ?", (USERNAME,))

print("所有测试用例通过！")