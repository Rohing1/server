import requests

host = "http://74.211.106.43:4584"
base = "/EOl1FEeG4PURunvh9s"
token = "3tuWiJ0UX7DK7CzxdL0lEjjuxc653hX5KO"

# 1. 测试不同的 API 路径 (clients/list vs inbounds/list)
paths = [
    "/panel/api/clients/list",
    "/panel/api/inbounds/list"
]

# 2. 测试不同的 Token 传递方式
headers_list = [
    {"Authorization": f"Bearer {token}"},  # 标准 Bearer
    {"Authorization": token},  # 纯 Token
    {"X-Api-Token": token}  # 自定义 Header
]

print("🔍 开始自动探测 3x-ui API...\n")

for path in paths:
    url = f"{host}{base}{path}"
    print(f"▶️ 尝试路径: {url}")

    # 测试 Header 传 Token
    for headers in headers_list:
        try:
            r = requests.get(url, headers=headers, timeout=5)
            print(f"   - Header传参 -> 状态码: {r.status_code}")
            if r.status_code == 200 and r.text:
                print(f"   ✅ 成功！返回内容: {r.text[:100]}...")
                print("🎉 找到正确姿势了！请看上面的 Header 和 Path！")
        except Exception as e:
            print(f"   ❌ 报错: {e}")

    # 测试 URL 传 Token
    url_with_token = f"{url}?token={token}"
    try:
        r = requests.get(url_with_token, timeout=5)
        print(f"   - URL传参 (?token=...) -> 状态码: {r.status_code}")
        if r.status_code == 200 and r.text:
            print(f"   ✅ 成功！返回内容: {r.text[:100]}...")
            print("🎉 找到正确姿势了！原来是 URL 传参！")
    except Exception as e:
        print(f"   ❌ 报错: {e}")

    print("-" * 50)