import logging
import os
from typing import Any
from urllib.parse import urljoin

import pymysql
import requests
from flask import Flask, jsonify, render_template

app = Flask(__name__)

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "127.0.0.1"),
    "port": int(os.getenv("DB_PORT", "3306")),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "123456"),
    "database": os.getenv("DB_NAME", "subscription_db"),
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor,
}

PANEL_CLIENTS_PATH = "/panel/api/clients/list"
REQUEST_TIMEOUT_SECONDS = float(os.getenv("PANEL_REQUEST_TIMEOUT", "10"))

PANEL_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
}


def get_db_connection():
    return pymysql.connect(**DB_CONFIG)


def format_size(value: Any) -> str:
    try:
        size = max(float(value or 0), 0)
    except (TypeError, ValueError):
        size = 0

    units = ("B", "KB", "MB", "GB", "TB", "PB")
    unit_index = 0
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1

    if unit_index == 0:
        return f"{int(size)} B"
    return f"{size:.2f} {units[unit_index]}"


def make_error(message: str) -> dict[str, Any]:
    return {"success": False, "message": message, "users": []}


def normalize_panel_base(host: str, path: str) -> str:
    host = (host or "").strip().rstrip("/")
    path = (path or "").strip().strip("/")

    if not path:
        return f"{host}/"
    return f"{host}/{path}/"


def build_panel_url(host: str, path: str) -> str:
    return urljoin(normalize_panel_base(host, path), PANEL_CLIENTS_PATH.lstrip("/"))


def get_panel_session() -> requests.Session:
    session = requests.Session()
    session.trust_env = False
    return session


def fetch_panel_json(host: str, path: str, token: str) -> tuple[dict[str, Any] | None, str | None]:
    url = build_panel_url(host, path)
    headers = {**PANEL_HEADERS, "Authorization": f"Bearer {token}"}

    try:
        with get_panel_session() as session:
            response = session.get(url, headers=headers, timeout=REQUEST_TIMEOUT_SECONDS)
    except requests.exceptions.Timeout:
        return None, "请求超时"
    except requests.exceptions.ConnectionError:
        return None, "连接失败"
    except requests.RequestException as exc:
        logger.warning("Panel request failed: %s", exc)
        return None, "请求面板失败"

    logger.info("Panel request finished: status=%s", response.status_code)

    if response.status_code != 200:
        return None, f"面板拒绝访问(状态码:{response.status_code})"

    try:
        return response.json(), None
    except ValueError:
        logger.warning("Panel returned non-json response, preview=%r", response.text[:120])
        return None, "面板返回了非 JSON 数据"


def parse_traffic_data(data: dict[str, Any]) -> dict[str, Any]:
    if not data.get("success"):
        return make_error(f'面板 API 报错: {data.get("msg", "未知错误")}')

    users = []
    total_up_bytes = 0
    total_down_bytes = 0

    for user in data.get("obj") or []:
        traffic = user.get("traffic") or {}
        up = int(traffic.get("up") or 0)
        down = int(traffic.get("down") or 0)
        total = up + down

        total_up_bytes += up
        total_down_bytes += down

        users.append(
            {
                "email": user.get("email") or "Unknown",
                "up": format_size(up),
                "down": format_size(down),
                "total": format_size(total),
                "total_bytes": total,
            }
        )

    users.sort(key=lambda item: item["total_bytes"], reverse=True)

    return {
        "success": True,
        "users": users,
        "summary": {
            "user_count": len(users),
            "total_up": format_size(total_up_bytes),
            "total_down": format_size(total_down_bytes),
            "total_all": format_size(total_up_bytes + total_down_bytes),
        },
    }


def fetch_node_traffic(row: dict[str, Any]) -> dict[str, Any]:
    host = (row.get("panel_host") or "").strip()
    path = (row.get("panel_path") or "").strip()
    token = (row.get("panel_token") or "").strip()

    if not all([host, path, token]):
        return make_error("未配置面板信息")

    data, error = fetch_panel_json(host, path, token)
    if error:
        return make_error(error)

    return parse_traffic_data(data or {})


@app.route("/")
def index():
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM resource_management ORDER BY id ASC")
            data = cursor.fetchall()
        return render_template("index.html", data=data)
    except pymysql.MySQLError as exc:
        logger.exception("Database query failed")
        return (
            "<h2 style='color:red;'>数据库连接失败</h2>"
            f"<p>错误信息: {exc}</p>"
        ), 500
    finally:
        if connection:
            connection.close()


@app.route("/api/traffic/<int:node_id>")
def get_node_traffic(node_id: int):
    connection = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM resource_management WHERE id = %s", (node_id,))
            row = cursor.fetchone()

        if not row:
            return jsonify({"success": False, "message": "节点不存在"}), 404

        traffic_data = fetch_node_traffic(row)

        if not traffic_data["success"]:
            return jsonify(
                {"success": False, "message": traffic_data["message"]}
            ), 502

        users = traffic_data["users"]
        return jsonify(
            {
                "success": True,
                "summary": traffic_data["summary"],
                "users": users,
                "user_count": len(users),
            }
        )

    except pymysql.MySQLError:
        logger.exception("Database query failed")
        return jsonify({"success": False, "message": "数据库查询失败"}), 500
    except Exception:
        logger.exception("Unexpected error")
        return jsonify({"success": False, "message": "查询失败"}), 500
    finally:
        if connection:
            connection.close()


if __name__ == "__main__":
    debug = os.getenv("FLASK_DEBUG", "1") == "1"
    host = os.getenv("FLASK_HOST", "0.0.0.0")
    port = int(os.getenv("FLASK_PORT", "5000"))
    app.run(debug=debug, host=host, port=port)
