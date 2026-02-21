import requests
import os
import time

# 保持原有的环境变量名
USER_EMAIL = os.environ.get('USER_EMAIL')
USER_PASSWORD = os.environ.get('USER_PASSWORD')

def run_task():
    # 基础配置
    api_host = "api-1209.apitutu.com"
    api_base = f"https://{api_host}/gateway/tqt/cn"
    origin_site = "https://vip.taoqitu.pro"
    
    # 严格匹配 iPhone 抓包提供的浏览器指纹
    headers = {
        "Host": api_host,
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh-Hans;q=0.9",
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/143.0.7499.151 Mobile/15E148 Safari/604.1",
        "Origin": origin_site,
        "Referer": f"{origin_site}/",
        "Sec-Fetch-Site": "cross-site",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
        "Connection": "keep-alive"
    }

    # 使用 Session 对象，它会自动处理后续请求的 Cookie 携带
    session = requests.Session()

    try:
        # --- 1. 执行登录 (JSON 格式) ---
        print(f"🚀 正在登录账号: {USER_EMAIL}...")
        login_url = f"{api_base}/passport/auth/login"
        payload = {'email': USER_EMAIL, 'password': USER_PASSWORD}
        
        # 发送登录请求
        login_res = session.post(login_url, json=payload, headers=headers, timeout=15)
        
        try:
            login_json = login_res.json()
        except:
            print(f"❌ 登录响应无法解析，状态码: {login_res.status_code}")
            return

        token = login_json.get('data', {}).get('token')
        if not token:
            print(f"❌ 获取 Token 失败: {login_json.get('message', '未知错误')}")
            return
        
        print("✅ 登录成功！已提取授权码")
        
        # --- 核心修正：双重身份注入 ---
        # 1. 注入 Header (不带 Bearer 前缀，匹配你最新的抓包)
        headers["Authorization"] = token
        
        # 2. 注入 Cookie (非常重要，很多面板后端强制检查 Cookie)
        session.cookies.set('auth_data', token, domain=api_host, path='/')
        session.cookies.set('authorization', token, domain=api_host, path='/')

        # 模拟人类操作延迟
        time.sleep(3)

        # --- 2. 执行签到 (GET) ---
        print("📝 发送签到指令...")
        sign_url = f"{api_base}/user/sign"
        # 使用 session 发送请求，它会自动带上刚才 set 的 Cookie
        sign_res = session.get(sign_url, headers=headers, timeout=15)
        
        try:
            sign_data = sign_res.json()
            message = sign_data.get('message', '未获取到提示')
            print(f"📣 签到反馈: {message}")
        except:
            print(f"⚠️ 响应异常，状态码: {sign_res.status_code}")
            print(f"预览: {sign_res.text[:100]}")

        # --- 3. 自动抵消流量 ---
        # 只要不是 403 错误，就尝试进行流量抵消
        if sign_res.status_code == 200:
            time.sleep(1)
            print("🔄 正在查询流量列表并抵消...")
            list_res = session.get(f"{api_base}/user/getSignList", headers=headers)
            list_data = list_res.json().get('data', [])
            
            if list_data:
                today_flow = list_data[0].get('get_num')
                print(f"📊 今日可抵消流量: {today_flow}GB")
                
                # 执行抵消动作
                convert_res = session.get(f"{api_base}/user/convertSign", headers=headers, params={'convert_num': today_flow})
                print(f"🎁 抵消操作结果: {convert_res.json().get('message', '完成')}")
            else:
                print("⚠️ 未发现可抵消流量记录")

    except Exception as e:
        print(f"💥 运行崩溃: {str(e)}")

if __name__ == "__main__":
    run_task()
