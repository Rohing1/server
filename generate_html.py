import pymysql

# ================= 配置区 =================
# 请根据你的实际数据库信息修改以下配置
DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 3306,
    'user': 'root',          # 数据库用户名
    'password': '123456', # 数据库密码
    'database': 'subscription_db',  # 数据库名称
    'charset': 'utf8mb4'
}
# ==========================================

def fetch_data():
    """连接数据库并查询数据"""
    connection = pymysql.connect(**DB_CONFIG, cursorclass=pymysql.cursors.DictCursor)
    try:
        with connection.cursor() as cursor:
            sql = "SELECT * FROM resource_management ORDER BY id DESC"
            cursor.execute(sql)
            result = cursor.fetchall()
            return result
    finally:
        connection.close()

def generate_html(data):
    """将数据渲染为 HTML 字符串"""
    # HTML 头部，引入 Bootstrap 5 让表格更美观
    html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>资源管理面板</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background-color: #f8f9fa; }
        .table th { background-color: #343a40; color: white; }
        .code-tag { font-family: monospace; background: #e9ecef; padding: 2px 5px; border-radius: 3px; font-size: 0.9em;}
    </style>
</head>
<body>
    <div class="container mt-5">
        <h2 class="mb-4 text-center">📊 资源管理列表</h2>
        <div class="table-responsive shadow-sm bg-white rounded">
            <table class="table table-striped table-hover align-middle">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>项目</th>
                        <th>团队</th>
                        <th>名称</th>
                        <th>价格(CNY)</th>
                        <th>价格(USD)</th>
                        <th>流量/月</th>
                        <th>节点地址</th>
                        <th>IP</th>
                        <th>中转</th>
                        <th>供应商</th>
                        <th>套餐名称</th>
                    </tr>
                </thead>
                <tbody>
"""
    
    # 遍历数据生成表格行
    for row in data:
        # 处理可能为 None 的字段，显示为 '-'
        team = row['team_name'] or '-'
        traffic = row['traffic_limit'] or '-'
        location = row['server_location'] or '-'
        ip = f'<span class="code-tag">{row["ip_address"]}</span>' if row['ip_address'] else '-'
        relay = f'<span class="code-tag">{row["relay_address"]}</span>' if row['relay_address'] else '-'
        provider = row['provider'] or '-'
        package_name = row['package_name'] or '-'
        
        # 格式化价格
        price_cny = f"¥{row['price_cny']}" if row['price_cny'] else '-'
        price_usd = f"${row['price_usd']}" if row['price_usd'] else '-'

        html += f"""
                    <tr>
                        <td>{row['id']}</td>
                        <td>{row['project_name']}</td>
                        <td>{team}</td>
                        <td><strong>{row['resource_name']}</strong></td>
                        <td>{price_cny}</td>
                        <td>{price_usd}</td>
                        <td>{traffic}</td>
                        <td>{location}</td>
                        <td>{ip}</td>
                        <td>{relay}</td>
                        <td>{provider}</td>
                        <td>{package_name}</td>
                    </tr>
        """
    
    # HTML 尾部
    html += """
                </tbody>
            </table>
        </div>
        <p class="text-muted text-center mt-3">数据生成时间: <script>document.write(new Date().toLocaleString())</script></p>
    </div>
</body>
</html>"""
    return html

if __name__ == '__main__':
    print("正在连接数据库...")
    data = fetch_data()
    print(f"查询成功，共获取 {len(data)} 条数据。")
    
    print("正在生成 HTML 文件...")
    html_content = generate_html(data)
    
    # 写入文件
    output_file = 'resource_management.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
        
    print(f"✅ 成功！请在当前目录下打开 {output_file} 查看结果。")