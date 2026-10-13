"""
聊天记录Model(Repository)
把对Messages表的SQL收拢到MessageRepository.
controller/Service不直接写SQL，统一通过本类访问。
和UserRepository是同一种分层思路。

用户隔离是本模块的核心约束：
所有读写方法都必须带username参数并放进where条件。
从而保证每个登录用户只能看到/写入自己的对话数据。
"""
from typing import Dict,List,Optional
from app.models.db import get_connection

class MessageRepository:
    @staticmethod
    def save(username:str,role:str,content:str):
        # role:user/assistant
        # content:消息正文
        with get_connection() as conn:
            cursor = conn.execute(
            """
                INSERT INTO messages (username,role,content) VALUES (?,?,?)
                """
                ,(username,role,content)
            )
            return cursor.lastrowid

    @staticmethod
    def list_recent(username:str,limit:int = 50) -> List[Dict]:
        with get_connection() as conn:
            rows = conn.execute(
            """
            SELECT role,content,created_at FROM (
             select id,role,content,created_at from messages where username = ?
             order by id Desc limit ?
            ) ORDER BY id ASC
            """,
            (username,limit)
        ).fetchall()
            return [dict(row) for row in rows]

    @staticmethod
    def count(username: Optional[str] = None) -> int:
        with get_connection() as conn:
            if username is None:
                row = conn.execute("select count(id) as c from messages").fetchone()
            else:
                row = conn.execute("select count(id) as c from messages where username = ?",(username,)).fetchone()
            return row["c"]