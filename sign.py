import requests
import os
import time

# 从 GitHub Secrets 中获取变量
USER_EMAIL = os.environ.get('USER_EMAIL')
USER_PASSWORD = os.environ.get('USER_PASSWORD')

def run_task():
    # 核心配置
    api_host = "api-1209.apitutu.com"
    api_base = f"https://{api_host}/gateway/tqt/cn"
    origin_site = "https://vip.taoqitu.pro"
    
    # 严格匹配 iPhone 成功抓包的 Header 指纹
    headers = {
        "Host": api_host,
        "Accept": "*/*",
        "Accept-Language": "zh-CN,zh-Hans;q=0.9",
        "Accept-Encoding": "gzip, deflate", # 移除 br 防止 Python 环境报错
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 26_3_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/143.0.7499.151 Mobile/15E148 Safari/604.1",
        "Origin": origin_site,
        "Referer": f"{origin_site}/",
        "Sec-Fetch-Site": "cross-site",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
        "Connection": "keep-alive",
        "Content-Type": "application/json"
    }

    session = requests.Session()

    try:
        # --- 1. 执行登录 ---
        print(f"🚀 正在登录账号: {USER_EMAIL}...")
        login_url = f"{api_base}/passport/auth/login"
        payload = {'email': USER_EMAIL, 'password': USER_PASSWORD}
        
        # 使用 JSON 负载登录
        login_res = session.post(login_url, json=payload, headers=headers, timeout=15)
        login_json = login_res.json()

        token = login_json.get('data', {}).get('token')
        if not token:
            print(f"❌ 登录失败: {login_json.get('message', '提取 Token 失败')}")
            return
        
        print("✅ 登录成功！正在准备签到...")
        
        # 核心修正：直接注入 JWT Token，不加 Bearer
        headers["Authorization"] = token

        # 模拟人类操作停顿
        time.sleep(2)

        # --- 2. 执行签到 (GET) ---
        print("📝 发送签到指令...")
        sign_url = f"{api_base}/user/sign"
        sign_res = session.get(sign_url, headers=headers, timeout=15)
        
        try:
            sign_data = sign_res.json()
            message = sign_data.get('message', '完成')
            print(f"🎉 签到结果反馈: {message}")
        except:
            print(f"⚠️ 响应解析异常: {sign_res.text[:100]}")

        # --- 3. 自动流量抵消 ---
        # 只要登录成功，就尝试查询并抵消
        time.sleep(1)
        print("🔄 正在同步执行流量抵消...")
        list_res = session.get(f"{api_base}/user/getSignList", headers=headers)
        list_data = list_res.json().get('data', [])
        
        if list_data:
            flow_val = list_data[0].get('get_num')
            print(f"📊 今日签到流量: {flow_val}GB，正在抵消...")
            
            # 抵消接口 (convertSign)
            convert_res = session.get(f"{api_base}/user/convertSign", headers=headers, params={'convert_num': flow_val})
            print(f"🎁 抵消结果: {convert_res.json().get('message', '执行完毕')}")
        else:
            print("ℹ️ 未发现可抵消流量")

    except Exception as e:
        print(f"💥 运行崩溃: {str(e)}")

if __name__ == "__main__":
    run_task()
