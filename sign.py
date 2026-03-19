import requests
import os
import time

# 1. 从环境变量获取配置
USERNAME = os.environ.get('USERNAME')
PASSWORD = os.environ.get('PASSWORD')
ENABLE_OFFSET = os.environ.get('ENABLE_OFFSET', 'false')

def run_task():
    if not USERNAME or not PASSWORD:
        print("❌ 错误: 未检测到 USERNAME 或 PASSWORD环境变量！")
        return

    api_host = "api-20260304.apitutu.com"
    api_base = f"https://{api_host}/gateway/tqt/cn"
    origin_site = "https://vip.taoqitu.pro"
    
    headers = {
        "Host": api_host,
        "Accept": "*/*",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate", 
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36",
        "Content-Type": "application/json",
        "Origin": origin_site,
        "Referer": f"{origin_site}/",
        "Connection": "keep-alive",
        "Sec-Ch-Ua": '"Not:A-Brand";v="99", "Google Chrome";v="145", "Chromium";v="145"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"macOS"',
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "cross-site"
    }

    session = requests.Session()

    try:
        # ==========================================
        # 步骤一：使用账号密码动态登录获取 Token
        # ==========================================
        print(f"🔐 正在尝试为账号 [{USERNAME[:3]}***] 登录...")
        
        login_url = f"{api_base}/passport/auth/login"
        login_payload = {
            "email": USERNAME,   
            "password": PASSWORD 
        }

        login_res = session.post(login_url, json=login_payload, headers=headers, timeout=15)
        
        if login_res.status_code != 200:
            print(f"❌ 登录网络请求失败，状态码: {login_res.status_code}")
            return

        login_data = login_res.json()
        dynamic_token = None
        
        # 提取 Token
        if isinstance(login_data, dict) and login_data.get('data'):
            data_field = login_data['data']
            if isinstance(data_field, dict):
                dynamic_token = data_field.get('token') or data_field.get('authorization') or data_field.get('auth_data')
            elif isinstance(data_field, str): 
                dynamic_token = data_field

        if dynamic_token:
            print("✅ 登录成功，已动态获取最新 Token！")
            
            # --- 关键修复：确保 Token 格式正确 ---
            # 如果抓包发现的旧 Token 不是以 Bearer 开头，就直接用；如果是，就在前面补上
            auth_value = dynamic_token if dynamic_token.startswith("Bearer") else dynamic_token
            
            # 强制更新 Session 的 Headers，确保每次请求都带着它
            session.headers.update({"Authorization": auth_value})
            
            # 强制更新 Session 的 Cookies
            session.cookies.update({
                'auth_data': dynamic_token,
                'authorization': dynamic_token
            })
            
        else:
            print(f"❌ 提取 Token 失败！")
            return

        # ==========================================
        # 步骤二：执行每日签到
        # ==========================================
        print("🚀 开始执行签到任务...")
        time.sleep(2) # 增加一点延迟，确保服务器状态更新
        
        sign_url = f"{api_base}/user/sign"
        
        # 这里直接用 session.get，不用再单独传 headers 了，因为上面已经更新到 session 里了
        res = session.get(sign_url, timeout=10) 
        
        print(f"📊 签到状态码: {res.status_code}")
        if res.text.strip():
            try:
                data = res.json()
                msg = data.get('message', '无消息')
                print(f"🎉 签到反馈: {msg}")
            except:
                print(f"⚠️ 原始签到响应: {res.text[:100]}")

        # ==========================================
        # 步骤三：流量抵消逻辑
        # ==========================================
        if res.status_code == 200 or (res.text and "已签到" in res.text):
            if ENABLE_OFFSET.lower() != 'true':
                print(f"🛑 抵消功能未开启 (当前设置: {ENABLE_OFFSET})，任务圆满结束。")
                return

            time.sleep(2) 
            print("🔄 抵消开关已开启，正在查询可抵消流量...")
            
            list_res = session.get(f"{api_base}/user/getSignList", timeout=10)
            
            try:
                list_data = list_res.json().get('data', [])
                if list_data and isinstance(list_data, list):
                    first_item = list_data[0]
                    flow_val = first_item.get('get_num')
                    is_convert = first_item.get('is_convert') 
                    
                    print(f"📊 最新待处理流量: {flow_val}GB (抵消状态: {is_convert})")
                    
                    if flow_val and is_convert == 0: 
                        convert_res = session.get(f"{api_base}/user/convertSign", params={'convert_num': flow_val})
                        print(f"🎁 抵消结果: {convert_res.json().get('message', '完成')}")
                    else:
                        print("ℹ️ 最新流量已被抵消过，跳过操作。")
                else:
                    print("ℹ️ 未查询到任何流量记录。")
            except Exception as e:
                print(f"⚠️ 获取流量列表或抵消失败: {e}")

    except Exception as e:
        print(f"💥 运行出错，异常信息: {str(e)}")

if __name__ == "__main__":
    run_task()
