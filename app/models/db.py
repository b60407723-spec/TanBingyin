"""
Sqlite数据访问层（Model层的基础设施）
本模块主要功能：
- 定位数据库文件路径
- 提供统一的连接工厂
- 应用启动时自动初始化数据库及表（如果不存在则创建）
"""
import os
import sqlite3
from contextlib import contextmanager
from typing import Iterator

def _project_root() -> str:
    """获取项目根目录"""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

#print(_project_root())  #输出项目根目录路径

# 数据库文件路径
DB_PATH = os.path.join(_project_root(), "database", "app.db")

# 数据库连接工厂（上下文管理器：with 块结束自动提交/回滚并关闭连接）
@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    """获取数据库连接；退出 with 块时自动提交（异常则回滚）并关闭连接"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)  # 确保数据库目录存在
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # 设置行工厂，使查询结果以字典形式返回
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    """初始化数据库及表"""
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
            );
            """
        )
        # 聊天记录表
        conn.execute(
            """
            -- id,username,role,content,created_at
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL DEFAULT '',
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
            );
            """
        )