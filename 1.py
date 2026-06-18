import requests

host = "https://45.77.213.193:58868"
base = "//HO6heGtIAP4euCuCPj"

token = "Dl6pfCo8sNLCkXMVzPEGkkzoPsZopQkyoOPYydBOLwZAaeMp"

url = f"{host}{base}/panel/api/clients/list"

headers = {
    "Authorization": f"Bearer {token}"
}

r = requests.get(url, headers=headers)
data = r.json()

if data["success"]:
    print("用户流量统计：\n")

    for user in data["obj"]:
        email = user["email"]
        traffic = user.get("traffic", {})

        up = traffic.get("up", 0)
        down = traffic.get("down", 0)

        total = up + down

        print(f"用户: {email}")
        print(f"上传: {up/1024/1024:.2f} MB")
        print(f"下载: {down/1024/1024:.2f} MB")
        print(f"总计: {total/1024/1024:.2f} MB")
        print("-" * 40)
else:
    print("请求失败:", data)