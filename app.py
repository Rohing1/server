from flask import Flask, render_template
import pymysql

app = Flask(__name__)

# ================= 数据库配置区 =================
# ⚠️ 请根据你的实际情况修改以下配置
DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'root',  # 你的数据库用户名
    'password': '123456', # 数据库密码
    'database': 'subscription_db',  # 数据库名称
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}


# ==============================================

def get_db_connection():
    """获取数据库连接"""
    return pymysql.connect(**DB_CONFIG)


@app.route('/')
def index():
    """主页路由：查询数据并渲染页面"""
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # 查询所有数据，按 ID 倒序排列
            sql = "SELECT * FROM resource_management ORDER BY id ASC"
            cursor.execute(sql)
            data = cursor.fetchall()

        # 将数据传递给 HTML 模板
        return render_template('index.html', data=data)

    except pymysql.MySQLError as e:
        return f"<h2 style='color:red;'>数据库连接失败，请检查配置！</h2><p>错误信息: {e}</p>"
    finally:
        if connection:
            connection.close()


if __name__ == '__main__':
    # debug=True 会在代码修改后自动重启服务，方便开发调试
    app.run(debug=True, host='0.0.0.0', port=5000)