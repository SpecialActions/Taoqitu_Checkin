import cloudscraper
import os
import time
import json

# 从 GitHub Secrets 获取账号信息
USER_EMAIL = os.environ.get('USER_EMAIL')
USER_PASSWORD = os.environ.get('USER_PASSWORD')

def run_task():
    # 基础配置
    api_host = "api-1209.apitutu.com"
    api_base = f"https://{api_host}/gateway/tqt/cn"
    origin_site = "https://vip.taoqitu.pro"
    
    # 1. 创建抗指纹 Scraper (模拟 Chrome 浏览器)
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'ios',
            'desktop': False,
            'mobile': True
        }
    )

    # 2. 配置请求头 (严格匹配你的抓包数据)
    headers = {
        "Host": api_host,
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh-Hans;q=0.9",
        "Accept-Encoding": "gzip, deflate",
        "Origin": origin_site,
        "Referer": f"{origin_site}/",
        "Sec-Fetch-Site": "cross-site",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Dest": "empty",
        "Connection": "keep-alive",
        "Content-Type": "application/json"
    }

    try:
        # --- 步骤 1: 登录 ---
        print(f"🚀 [CloudScraper] 正在登录: {USER_EMAIL}...")
        login_url = f"{api_base}/passport/auth/login"
        payload = {'email': USER_EMAIL, 'password': USER_PASSWORD}
        
        # 使用 scraper 发送 POST 请求
        login_res = scraper.post(login_url, json=payload, headers=headers)
        
        try:
            login_json = login_res.json()
        except:
            print(f"❌ 登录失败，可能遇到 Cloudflare 验证。")
            print(f"状态码: {login_res.status_code}")
            print(f"返回内容: {login_res.text[:200]}")
            return

        # 提取 Token
        token = login_json.get('data', {}).get('token')
        if not token:
            print(f"❌ 登录失败: {login_json.get('message', '账号或密码错误')}")
            return
        
        print("✅ 登录成功！")
        
        # 设置身份凭证 (Header + Cookie 双重保险)
        headers["Authorization"] = token
        scraper.cookies.set('auth_data', token, domain=api_host)
        scraper.cookies.set('authorization', token, domain=api_host)

        time.sleep(3) # 稍作等待

        # --- 步骤 2: 签到 ---
        print("📝 发送签到请求...")
        sign_url = f"{api_base}/user/sign"
        sign_res = scraper.get(sign_url, headers=headers)
        
        try:
            sign_data = sign_res.json()
            print(f"📣 签到反馈: {sign_data.get('message', '无返回消息')}")
        except:
            print(f"⚠️ 签到响应异常: {sign_res.text[:100]}")

        # --- 步骤 3: 自动抵消流量 ---
        # 只要状态码正常，就尝试去抵消流量
        if sign_res.status_code == 200:
            time.sleep(2)
            print("🔄 查询流量并执行抵消...")
            list_res = scraper.get(f"{api_base}/user/getSignList", headers=headers)
            
            try:
                list_data = list_res.json().get('data', [])
                if list_data:
                    # 获取最新的一条签到记录流量
                    flow = list_data[0].get('get_num')
                    print(f"📊 今日获取流量: {flow}GB")
                    
                    # 执行抵消
                    convert_res = scraper.get(f"{api_base}/user/convertSign", headers=headers, params={'convert_num': flow})
                    print(f"🎁 抵消结果: {convert_res.json().get('message', '完成')}")
                else:
                    print("ℹ️ 未查询到可抵消的流量记录")
            except:
                print("⚠️ 获取流量列表失败")

    except Exception as e:
        print(f"💥 运行崩溃: {str(e)}")

if __name__ == "__main__":
    run_task()
