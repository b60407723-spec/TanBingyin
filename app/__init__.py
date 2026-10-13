"""app包：Tornado + Agentica + Sqlite3智能体的业务代码入口
MVC三层架构：
• controllers: 控制层，主要是Tornado RequestHandler

• services: 服务层，主要是Agentica智能体组装与调度及其他业务服务

• models: 数据模型层，主要是SQLAlchemy ORM模型

• views: 视图层，主要是HTML模板文件

"""