import requests
import os
import time

# 环境变量获取
USER_EMAIL = os.environ.get('USER_EMAIL')
USER_PASSWORD = os.environ.get('USER_PASSWORD')

def run_task():
    api_host = "api-1209.apitutu.com"
    api_base = f"https://{api_host}/gateway/tqt/cn"
    origin_site = "https://vip.taoqitu.pro"
    
    # 完全匹配你抓包获取的 Headers，移除不必要的压缩声明以防解析失败
    headers = {
        "Host": api_host,
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh-Hans;q=0.9",
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/143.0.7499.151 Mobile/15E148 Safari/604.1",
        "Origin": origin_site,
        "Referer": f"{origin_site}/",
        "Content-Type": "application/json", # 明确使用 JSON 提交
        "Sec-Fetch-Site": "cross-site",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
        "Connection": "keep-alive"
    }

    session = requests.Session()

    try:
        # --- 1. 登录 ---
        print(f"🚀 正在尝试登录: {USER_EMAIL}...")
        login_url = f"{api_base}/passport/auth/login"
        # 抓包显示为 JSON 负载
        payload = {'email': USER_EMAIL, 'password': USER_PASSWORD}
        
        login_res = session.post(login_url, json=payload, headers=headers, timeout=15)
        
        if login_res.status_code != 200:
            print(f"❌ 登录接口状态异常: {login_res.status_code}")
            print(f"内容预览: {login_res.text[:100]}")
            return

        try:
            login_json = login_res.json()
        except:
            print("❌ 无法解析登录响应为 JSON，尝试打印原文:")
            print(login_res.text)
            return

        token = login_json.get('data', {}).get('token')
        if not token:
            print(f"❌ 登录未获取到 Token: {login_json.get('message', '未知错误')}")
            return
        
        print("✅ 登录成功！")
        headers["Authorization"] = token # 注入 JWT Token
        
        # --- 2. 签到 ---
        time.sleep(2) 
        print("📝 执行签到请求...")
        sign_res = session.get(f"{api_base}/user/sign", headers=headers, timeout=15)
        
        try:
            sign_data = sign_res.json()
            print(f"📣 签到反馈: {sign_data.get('message', '执行完毕')}")
        except:
            print(f"✅ 签到可能已完成，但响应不可读: {sign_res.text[:50]}")

        # --- 3. 抵消流量 ---
        if sign_res.status_code == 200:
            time.sleep(1)
            list_res = session.get(f"{api_base}/user/getSignList", headers=headers)
            list_data = list_res.json().get('data', [])
            if list_data:
                flow = list_data[0].get('get_num')
                print(f"📊 今日获得: {flow}GB，执行抵消...")
                conv_res = session.get(f"{api_base}/user/convertSign", headers=headers, params={'convert_num': flow})
                print(f"🎁 抵消结果: {conv_res.json().get('message', '完成')}")

    except Exception as e:
        print(f"💥 脚本崩溃: {str(e)}")

if __name__ == "__main__":
    run_task()
