# --*-- coding: utf-8 --*--

"""
@File: update_cookie.py
@Author: Gemini
@Date: 2025-10-01
@Description: 用于从指定API获取Cookie并更新到青龙面板环境变量的脚本。
@Version: 5.0
@Changes: 根据调试结果，修正了用于匹配Cookie的关键字，确保脚本能正确处理API返回的数据。
"""

import os
import requests
import json
import sys

# --- 全局配置 ---
UCC_URL = os.getenv("UCC")
CC_UUID = os.getenv("CC_UUID")
CC_PASSWORD = os.getenv("CC_PASSWORD")

# --- 核心功能函数 ---

def check_configs():
    """检查必要的环境变量是否已设置"""
    print("正在检查环境变量配置...")
    if not all([UCC_URL, CC_UUID, CC_PASSWORD]):
        print("错误：脚本所需的环境变量不完整！...")
        sys.exit(1)
    print("配置检查通过！")
    print(f"API 地址: {UCC_URL}")

def get_latest_cookies(base_url, uuid, password):
    """通过API获取最新的Cookie。"""
    api_url = f"{base_url}/get/{uuid}"
    headers = {"Content-Type": "application/json"}
    payload = {"password": password if password else ""}
    print(f"正在从 {api_url} 获取 Cookies...")
    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=15)
        if response.status_code == 200:
            print("成功获取 API 响应。")
            return response.json()
        else:
            print(f"错误：API 请求失败，状态码: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"错误：网络请求异常: {e}")
        return None

def format_any_cookie_style(data, cookie_type_name):
    """智能处理两种Cookie格式"""
    if isinstance(data, list):
        print(f"[{cookie_type_name}] 检测到标准JSON数组格式的Cookie，直接处理。")
        cookie_parts = [f'{cookie.get("name")}={cookie.get("value")}' for cookie in data if cookie.get("name") and cookie.get("value")]
        return "; ".join(cookie_parts)
    if not isinstance(data, str):
        print(f"警告: [{cookie_type_name}] 未知的Cookie数据类型: {type(data)}，无法处理。")
        return ""
    print(f"[{cookie_type_name}] 检测到字符串格式的Cookie，尝试修复并解析...")
    fixed_string = data.strip()
    if not (fixed_string.startswith('[') and fixed_string.endswith(']')):
        json_array_string = f"[{fixed_string}]"
    else:
        json_array_string = fixed_string
    try:
        cookie_list = json.loads(json_array_string)
        print(f"[{cookie_type_name}] 字符串成功解析为JSON数组。")
        return format_any_cookie_style(cookie_list, cookie_type_name)
    except json.JSONDecodeError:
        print(f"警告: [{cookie_type_name}] 尝试将字符串解析为JSON数组失败。")
        return ""

def update_ql_env(env_name, new_value):
    """使用青龙内置的 QLAPI 更新环境变量。"""
    try:
        print(f"\n--- 开始更新变量: {env_name} ---")
        print(f"正在查询青龙环境变量: {env_name}")
        search_result = QLAPI.getEnvs({"searchValue": env_name})
        if search_result.get("code") != 200: return
        target_env = None
        if search_result.get("data"):
            for env in search_result.get("data"):
                if env.get("name") == env_name: target_env = env; break
        if not target_env: print(f"错误：未找到名为 '{env_name}' 的环境变量。"); return
        env_id = target_env.get("id") or target_env.get("_id")
        if not env_id: print(f"错误：无法获取环境变量 ID。"); return
        print(f"已找到目标变量，ID: {env_id}")
        env_item_payload = {"id": env_id, "_id": env_id, "name": env_name, "value": new_value, "remarks": target_env.get("remarks", "")}
        final_payload = {"env": env_item_payload}
        print("正在提交更新请求...")
        update_result = QLAPI.updateEnv(final_payload)
        if update_result.get("code") == 200: print(f"✅ 环境变量 '{env_name}' 更新成功！")
        else: print(f"❌ 环境变量 '{env_name}' 更新失败！ API响应: {update_result.get('message', '无详细信息')}")
    except Exception as e:
        print(f"更新环境变量时发生未知错误: {e}")

# --- 主逻辑 ---
if __name__ == "__main__":
    check_configs()
    cookie_data_json = get_latest_cookies(UCC_URL, CC_UUID, CC_PASSWORD)

    if not cookie_data_json or "cookie_data" not in cookie_data_json:
        print("未能获取有效的 Cookie 数据，脚本终止。")
        sys.exit(1)
        
    all_cookies = cookie_data_json.get("cookie_data", {})
    updated = False

    # 最终修正：使用从调试日志中发现的正确关键字
    nodeseek_key = "www.nodeseek.com"
    enshanck_key = "www.right.com.cn"

    # 逻辑1: 检查 'www.nodeseek.com' 并更新 'NS_COOKIE'
    if nodeseek_key in all_cookies:
        updated = True
        ns_cookie_value = format_any_cookie_style(all_cookies[nodeseek_key], nodeseek_key)
        if ns_cookie_value:
            update_ql_env("NS_COOKIE", ns_cookie_value)
        else:
            print(f"'{nodeseek_key}' 的 Cookie 数据为空或格式错误，不执行更新。")

    # 逻辑2: 检查 'www.right.com.cn' 并更新 'ENSHANCK'
    if enshanck_key in all_cookies:
        updated = True
        enshanck_cookie_value = format_any_cookie_style(all_cookies[enshanck_key], enshanck_key)
        if enshanck_cookie_value:
            update_ql_env("ENSHANCK", enshanck_cookie_value)
        else:
            print(f"'{enshanck_key}' 的 Cookie 数据为空或格式错误，不执行更新。")
    
    if not updated:
        print(f"\n在返回的数据中未发现 '{nodeseek_key}' 或 '{enshanck_key}' 相关的Cookie，本次无需更新。")

    print("\n脚本执行完毕。")
