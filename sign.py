import requests
import os
import time
import json

# 优先读取 USER_TOKEN，如果没有则使用账号密码
USER_TOKEN = os.environ.get('USER_TOKEN')
USER_EMAIL = os.environ.get('USER_EMAIL')
USER_PASSWORD = os.environ.get('USER_PASSWORD')

def run_task():
    api_host = "api-1209.apitutu.com"
    api_base = f"https://{api_host}/gateway/tqt/cn"
    origin_site = "https://vip.taoqitu.pro"
    
    # 这里的 User-Agent 必须和你抓包获取 Token 的设备一致（iPhone）
    headers = {
        "Host": api_host,
        "Accept": "*/*",
        "Accept-Language": "zh-CN,zh-Hans;q=0.9",
        "Accept-Encoding": "gzip, deflate",
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
    
    # --- 策略分支 ---
    auth_token = None
    
    # 策略 A: 优先使用手动提供的 Token (避开登录风控)
    if USER_TOKEN and len(USER_TOKEN) > 50:
        print(f"💎 检测到 USER_TOKEN，跳过登录步骤，直接使用凭证签到...")
        auth_token = USER_TOKEN
    
    # 策略 B: 尝试账号密码登录 (容易被风控)
    elif USER_EMAIL and USER_PASSWORD:
        print(f"🚀 未找到 USER_TOKEN，尝试使用账号 {USER_EMAIL} 登录...")
        try:
            login_url = f"{api_base}/passport/auth/login"
            payload = {'email': USER_EMAIL, 'password': USER_PASSWORD}
            login_res = session.post(login_url, json=payload, headers=headers, timeout=15)
            
            # 调试打印
            if login_res.status_code != 200:
                print(f"❌ 登录请求失败: {login_res.status_code}")
                print(login_res.text)
                return

            token = login_res.json().get('data', {}).get('token')
            if token:
                print("✅ 登录成功！(注意：此 IP 生成的 Token 可能会被风控)")
                auth_token = token
            else:
                print(f"❌ 登录失败: {login_res.json().get('message')}")
                return
        except Exception as e:
            print(f"💥 登录过程出错: {e}")
            return
    else:
        print("❌ 错误: 未配置 USER_TOKEN 或 账号密码")
        return

    # --- 执行签到 ---
    if auth_token:
        # 注入 Token
        headers["Authorization"] = auth_token
        
        # 强制同步 Cookie (以此来通过部分后端校验)
        session.cookies.set('auth_data', auth_token, domain=api_host)
        
        time.sleep(2)
        print("📝 发送签到请求...")
        try:
            sign_url = f"{api_base}/user/sign"
            sign_res = session.get(sign_url, headers=headers, timeout=15)
            
            print(f"📊 状态码: {sign_res.status_code}")
            try:
                print(f"📣 反馈信息: {sign_res.json()}")
            except:
                print(f"⚠️ 原始响应: {sign_res.text[:100]}")

            # --- 自动抵消流量 ---
            # 即使签到返回“已签到”，只要 Token 有效，就可以查流量
            if sign_res.status_code == 200 or "已签到" in sign_res.text:
                time.sleep(1)
                print("🔄 正在查询流量并抵消...")
                list_res = session.get(f"{api_base}/user/getSignList", headers=headers)
                list_data = list_res.json().get('data', [])
                
                if list_data:
                    flow = list_data[0].get('get_num')
                    print(f"📊 今日待抵消: {flow}GB")
                    convert_res = session.get(f"{api_base}/user/convertSign", headers=headers, params={'convert_num': flow})
                    print(f"🎁 抵消结果: {convert_res.json().get('message', '完成')}")
                else:
                    print("ℹ️ 未查到流量记录 (可能 Token 权限不足或无记录)")
                    
        except Exception as e:
            print(f"💥 签到过程出错: {e}")

if __name__ == "__main__":
    run_task()
