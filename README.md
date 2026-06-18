# Flask MySQL 资源展示系统

这是一个基于 Python Flask 框架和 MySQL 数据库构建的轻量级 Web 应用程序。该项目主要用于从 MySQL 数据库的 `resource_management` 表中读取数据，并将其渲染展示在前端 HTML 页面上。

## 🛠️ 技术栈

- **后端框架**: Flask
- **数据库驱动**: PyMySQL
- **数据库**: MySQL (5.7 / 8.0+)
- **语言**: Python 3.8+

## 📋 功能特性

- 连接本地或远程 MySQL 数据库。
- 查询 `resource_management` 表中的所有数据。
- 将查询结果按 ID 升序排列并传递给前端模板。
- 包含基础的数据库异常捕获与错误提示。

## 🚀 快速开始

### 1. 环境准备

确保您的系统已安装以下软件：

- Python 3.8 或更高版本
- MySQL 数据库服务

### 2. 安装依赖

建议使用 Python 虚拟环境来隔离项目依赖：

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 安装必要的库
pip install flask pymysql
```
```bash
DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'root',  
    'password': '您的真实数据库密码', # ⚠️ 修改这里
    'database': 'subscription_db',  
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}
```
