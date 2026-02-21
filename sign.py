import requests
import os
import time

# 只读取 Token，不再尝试账号密码登录（避免风控）
USER_TOKEN = os.environ.get('USER_TOKEN')

def run_task():
    if not USER_TOKEN:
        print("❌ 错误: 未检测到 USER_TOKEN，请在 GitHub Secrets 中添加！")
        return

    # 基础配置
    api_host = "api-1209.apitutu.com"
    api_base = f"https://{api_host}/gateway/tqt/cn"
    origin_site = "https://vip.taoqitu.pro"
    
    # 🌟 核心修正：伪装成 Mac 电脑 Chrome 浏览器 (与你截图一致)
    headers = {
        "Host": api_host,
        "Accept": "*/*",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Accept-Encoding": "gzip, deflate", # 只要 gzip，不要 br (防止 Python 解压失败)
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Origin": origin_site,
        "Referer": f"{origin_site}/",
        "Authorization": USER_TOKEN,  # 直接注入 Token
        "Connection": "keep-alive",
        # 模拟桌面端特有的 Sec 字段
        "Sec-Ch-Ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"macOS"',
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "cross-site"
    }

    session = requests.Session()

    # 🌟 核心修正：手动强制注入 Cookie
    # V2Board 经常检查 cookie 里的 auth_data 是否与 header 里的 Authorization 一致
    cookie_dict = {
        'auth_data': USER_TOKEN,
        'authorization': USER_TOKEN
    }
    session.cookies.update(cookie_dict)

    try:
        print("🚀 [Desktop模式] 使用 Token 直接签到...")
        
        # --- 1. 执行签到 ---
        sign_url = f"{api_base}/user/sign"
        # 使用 session 发送请求，它会自动带上 Cookie
        res = session.get(sign_url, headers=headers, timeout=10)
        
        print(f"📊 状态码: {res.status_code}")
        
        try:
            # 尝试解析 JSON
            data = res.json()
            msg = data.get('message', '无消息')
            print(f"🎉 签到反馈: {msg}")
        except:
            # 如果不是 JSON (比如报错 HTML)，打印前 100 个字符
            print(f"⚠️ 原始响应: {res.text[:200]}")

        # --- 2. 自动抵消流量 ---
        # 只要状态码是 200，或者提示“已签到”，都去尝试抵消
        if res.status_code == 200 or (res.text and "已签到" in res.text):
            time.sleep(1)
            print("🔄 正在查询流量并执行抵消...")
            
            # 获取流量列表
            list_res = session.get(f"{api_base}/user/getSignList", headers=headers, timeout=10)
            list_data = list_res.json().get('data', [])
            
            if list_data:
                # 获取最新的一条流量数值
                flow_val = list_data[0].get('get_num')
                print(f"📊 待抵消流量: {flow_val}GB")
                
                # 发送抵消请求
                convert_res = session.get(f"{api_base}/user/convertSign", headers=headers, params={'convert_num': flow_val})
                print(f"🎁 抵消结果: {convert_res.json().get('message', '完成')}")
            else:
                print("ℹ️ 未查询到可抵消的流量记录")

    except Exception as e:
        print(f"💥 运行出错: {str(e)}")

if __name__ == "__main__":
    run_task()
