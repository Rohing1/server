from flask import Flask, render_template, jsonify
import pymysql
import requests

app = Flask(__name__)

# ================= 数据库配置区 =================
DB_CONFIG = {
    'host': '192.168.1.1',
    'port': 3306,
    'user': 'root',
    'password': '123456@2026',
    'database': 'subscription_db',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}


def get_db_connection():
    return pymysql.connect(**DB_CONFIG)


def format_size(bytes_val):
    if bytes_val < 1024 ** 3:
        return f"{bytes_val / 1024 ** 2:.2f} MB"
    return f"{bytes_val / 1024 ** 3:.2f} GB"


def fetch_node_traffic(row):
    """查询单个节点的流量数据。"""
    host = row.get('panel_host', '').strip()
    path = row.get('panel_path', '').strip()
    token = row.get('panel_token', '').strip()

    row['traffic_data'] = {'success': False, 'message': '未配置面板信息', 'users': []}
    if not all([host, path, token]):
        return row

    url = f"{host}{path}/panel/api/clients/list"

    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*"
    }

    try:
        # 强制不走任何代理，直接连接服务器。
        r = requests.get(url, headers=headers, timeout=10, proxies={"http": None, "https": None})

        print(f"\n--- 3x-ui 响应详情 ---")
        print(f"请求 URL: {url}")
        print(f"HTTP 状态码: {r.status_code}")
        print(f"返回内容前100字: {r.text[:100]}")
        print(f"----------------------\n")

        if r.status_code != 200:
            row['traffic_data'] = {'success': False, 'message': f'面板拒绝访问(状态码:{r.status_code})', 'users': []}
            return row

        try:
            data = r.json()
        except ValueError:
            row['traffic_data'] = {'success': False, 'message': '面板返回了非JSON数据', 'users': []}
            return row

        if data.get("success"):
            users = []
            total_up_bytes = 0
            total_down_bytes = 0

            for user in data.get("obj", []):
                email = user.get("email", "Unknown")
                traffic = user.get("traffic", {})
                up = traffic.get("up", 0)
                down = traffic.get("down", 0)
                total = up + down

                total_up_bytes += up
                total_down_bytes += down

                users.append({
                    "email": email,
                    "up": format_size(up),
                    "down": format_size(down),
                    "total": format_size(total),
                    "total_bytes": total
                })

            users.sort(key=lambda x: x["total_bytes"], reverse=True)

            summary = {
                "user_count": len(users),
                "total_up": format_size(total_up_bytes),
                "total_down": format_size(total_down_bytes),
                "total_all": format_size(total_up_bytes + total_down_bytes)
            }

            row['traffic_data'] = {'success': True, 'users': users, 'summary': summary}
        else:
            row['traffic_data'] = {
                'success': False,
                'message': f'面板API报错: {data.get("msg", "未知错误")}',
                'users': []
            }

    except requests.exceptions.Timeout:
        row['traffic_data'] = {'success': False, 'message': '请求超时', 'users': []}
    except requests.exceptions.ConnectionError:
        row['traffic_data'] = {'success': False, 'message': '连接失败', 'users': []}
    except Exception as e:
        row['traffic_data'] = {'success': False, 'message': f'未知异常: {str(e)}', 'users': []}

    return row


# ================= 路由 1：主页 =================
@app.route('/')
def index():
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            sql = "SELECT * FROM resource_management ORDER BY id ASC"
            cursor.execute(sql)
            data = cursor.fetchall()
        return render_template('index.html', data=data)
    except pymysql.MySQLError as e:
        return f"<h2 style='color:red;'>数据库连接失败！</h2><p>错误信息: {e}</p>"
    finally:
        if connection:
            connection.close()


# ================= 路由 2：API 接口 =================
@app.route('/api/traffic/<int:node_id>')
def get_node_traffic(node_id):
    """API接口：获取单个节点的实时流量数据。"""
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            sql = "SELECT * FROM resource_management WHERE id = %s"
            cursor.execute(sql, (node_id,))
            row = cursor.fetchone()

        if not row:
            return jsonify({'success': False, 'message': '节点不存在'})

        result = fetch_node_traffic(row)

        if result['traffic_data']['success']:
            return jsonify({
                'success': True,
                'summary': result['traffic_data']['summary'],
                'users': result['traffic_data']['users'],
                'user_count': len(result['traffic_data']['users'])
            })
        return jsonify({'success': False, 'message': result['traffic_data']['message']})

    except Exception as e:
        return jsonify({'success': False, 'message': f'查询失败: {str(e)}'})
    finally:
        if connection:
            connection.close()


# ================= 启动服务 =================
if __name__ == '__main__':
    # 注意：所有的 @app.route 必须写在这行代码的上面。
    app.run(debug=True, host='0.0.0.0', port=5000)
