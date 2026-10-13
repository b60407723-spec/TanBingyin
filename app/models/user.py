"""
user模型(Repository模式)
把对users表的所有SQL收拢到UserRepository中，作为数据访问层的封装，
上层controller只需要调用UserRepository提供的接口即可，不需要关心具体的SQL语句
要点：
1、不存明文密码，存储密码的hash值和salt
2、登录时用同一个salt对用户输入的密码进行hash，然后和数据库中存储的hash值进行比对
3、username有UNIQUE约束，不能重复，重名插入会抛sqlite3.IntegrityError异常
"""
import hashlib
import secrets
import sqlite3
from typing import Optional
from app.models.db import get_connection

_PBKDF2_ITERATIONS = 100_000  # PBKDF2迭代次数

#密文加盐加密方法
def _hash_password(password: str, salt: str) -> str:
    digest = hashlib.pbkdf2_hmac(
        'sha256',  # 使用SHA-256哈希算法
        password.encode('utf-8'),
        salt,
        _PBKDF2_ITERATIONS
    )
    return digest.hex()

class UserRepository:
    """用户数据访问层"""
    @staticmethod
    def create_user(username:str, password:str) -> bool:
        salt = secrets.token_bytes(16)  # 生成16字节的随机salt
        password_hash = _hash_password(password, salt)
        try:
            with get_connection() as conn:
                conn.execute(
                    "INSERT INTO users (username, password_hash, salt) VALUES (?, ?, ?)",
                    (username, password_hash, salt.hex())
                )
            return True
        except sqlite3.IntegrityError:
            return False  # 用户名已存在
        
    @staticmethod
    def get_user_by_username(username:str) -> Optional[sqlite3.Row]:
        with get_connection() as conn:
            return conn.execute(
                "SELECT * FROM users WHERE username = ?",
                (username,)
            ).fetchone()
        
    @staticmethod
    def verify_user(username:str, password:str) -> bool:
        user = UserRepository.get_user_by_username(username)
        if user is None:
            return False
        salt = bytes.fromhex(user['salt'])
        password_hash = _hash_password(password, salt)
        return password_hash == user['password_hash']    