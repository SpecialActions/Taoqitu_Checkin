import requests
import os
import time

# 保持原有的环境变量名
USER_EMAIL = os.environ.get('USER_EMAIL')
USER_PASSWORD = os.environ.get('USER_PASSWORD')

def run_task():
    # 核心配置
    api_host = "api-1209.apitutu.com"
    api_base = f"https://{api_host}/gateway/tqt/cn"
    origin_site = "https://vip.taoqitu.pro"
    
    # 完全匹配你提供的 iPhone 抓包 Header
    headers = {
        "Host": api_host,
        "Accept": "*/*",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "zh-CN,zh-Hans;q=0.9",
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 26_3_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/143.0.7499.151 Mobile/15E148 Safari/604.1",
        "Origin": origin_site,
        "Referer": f"{origin_site}/",
        "Sec-Fetch-Site": "cross-site",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
        "Connection": "keep-alive"
    }

    session = requests.Session()

    try:
        # --- 1. 执行登录 (Form Data 格式) ---
        print(f"🚀 正在登录: {USER_EMAIL}...")
        login_url = f"{api_base}/passport/auth/login"
        payload = {'email': USER_EMAIL, 'password': USER_PASSWORD}
        
        # 很多类似面板在后端接收时优先处理 Form Data
        login_res = session.post(login_url, data=payload, headers=headers)
        login_json = login_res.json()

        # 提取 Token
        token = login_json.get('data', {}).get('token') or login_json.get('data', {}).get('auth_data')

        if not token:
            print(f"❌ 登录失败: {login_json.get('message', '账号或密码错误')}")
            return
        
        print("✅ 登录成功！")
        
        # --- 关键修复：根据抓包显示，Authorization 不需要 Bearer 前缀 ---
        headers["Authorization"] = token
        
        # 模拟操作间隔
        time.sleep(2)

        # --- 2. 签到 (GET /user/sign) ---
        print("📝 正在发送签到指令...")
        sign_url = f"{api_base}/user/sign"
        sign_res = session.get(sign_url, headers=headers)
        
        try:
            sign_data = sign_res.json()
            message = sign_data.get('message', '操作完成')
            print(f"📣 签到反馈: {message}")
        except:
            print(f"⚠️ 无法解析响应，状态码: {sign_res.status_code}")
            print(f"原始响应文本: {sign_res.text}")

        # --- 3. 自动抵消流量 (convertSign) ---
        if sign_res.status_code == 200:
            time.sleep(1)
            print("🔄 正在自动执行流量抵消...")
            list_res = session.get(f"{api_base}/user/getSignList", headers=headers)
            list_data = list_res.json().get('data', [])
            
            if list_data:
                today_flow = list_data[0].get('get_num')
                print(f"📊 今日可抵消: {today_flow}GB")
                
                convert_res = session.get(f"{api_base}/user/convertSign", headers=headers, params={'convert_num': today_flow})
                print(f"🎁 抵消结果: {convert_res.json().get('message', '已完成')}")
            else:
                print("⚠️ 未发现流量记录")

    except Exception as e:
        print(f"💥 运行异常: {str(e)}")

if __name__ == "__main__":
    run_task()
