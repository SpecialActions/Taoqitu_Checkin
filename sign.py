import requests
import os
import time

# 1. 从环境变量获取配置 (请在 GitHub Secrets 中配置)
USERNAME = os.environ.get('USERNAME')
PASSWORD = os.environ.get('PASSWORD')
ENABLE_OFFSET = os.environ.get('ENABLE_OFFSET', 'false')

def run_task():
    if not USERNAME or not PASSWORD:
        print("❌ 错误: 未检测到 USERNAME 或 PASSWORD环境变量！")
        print("💡 请前往 GitHub 仓库 -> Settings -> Secrets and variables -> Actions 中添加。")
        return

    # API 基础配置 (基于最新抓包结果)
    api_host = "api-20260304.apitutu.com"
    api_base = f"https://{api_host}/gateway/tqt/cn"
    origin_site = "https://vip.taoqitu.pro"
    
    # 完美伪装 Mac Chrome 浏览器请求头
    headers = {
        "Host": api_host,
        "Accept": "*/*",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br, zstd",
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

        # 发起登录请求
        login_res = session.post(login_url, json=login_payload, headers=headers, timeout=15)
        
        # --- 强力排错逻辑：无论成败，先看看服务器到底返回了什么 ---
        try:
            login_data = login_res.json()
        except Exception as e:
            print(f"❌ 解析 JSON 失败！服务器可能拦截了 GitHub 的 IP (例如 Cloudflare 防护盾)。")
            print(f"📊 HTTP 状态码: {login_res.status_code}")
            print(f"🔍 服务器实际返回的原始内容如下 (前800字符):\n{login_res.text[:800]}")
            return
        
        # 检查 HTTP 状态码
        if login_res.status_code != 200:
            print(f"❌ 登录网络请求失败，状态码: {login_res.status_code}")
            return

        # 智能提取 Token 逻辑 (兼容不同的返回格式)
        dynamic_token = None
        if isinstance(login_data, dict) and login_data.get('data'):
            data_field = login_data['data']
            if isinstance(data_field, dict):
                dynamic_token = data_field.get('token') or data_field.get('authorization') or data_field.get('auth_data')
            elif isinstance(data_field, str): 
                dynamic_token = data_field

        if dynamic_token:
            print("✅ 登录成功，已动态获取最新 Token！")
            
            # 将新 Token 更新到请求头和 Cookie 中，供后续请求使用
            headers['Authorization'] = dynamic_token
            session.cookies.update({
                'auth_data': dynamic_token,
                'authorization': dynamic_token
            })
        else:
            print(f"❌ 提取 Token 失败！请检查账号密码是否正确。")
            print(f"🔍 服务器返回的 JSON 内容: {login_data}")
            return

        # ==========================================
        # 步骤二：执行每日签到
        # ==========================================
        print("🚀 开始执行签到任务...")
        time.sleep(1) # 稍微停顿，模拟人类操作
        
        sign_url = f"{api_base}/user/sign"
        res = session.get(sign_url, headers=headers, timeout=10)
        
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

            time.sleep(2) # 抵消前等待，防止请求过快被风控
            print("🔄 抵消开关已开启，正在查询可抵消流量...")
            
            list_res = session.get(f"{api_base}/user/getSignList", headers=headers, timeout=10)
            
            try:
                list_data = list_res.json().get('data', [])
                if list_data and isinstance(list_data, list):
                    first_item = list_data[0]
                    flow_val = first_item.get('get_num')
                    is_convert = first_item.get('is_convert') 
                    
                    print(f"📊 最新待处理流量: {flow_val}GB (抵消状态: {is_convert})")
                    
                    if flow_val and is_convert == 0: 
                        convert_res = session.get(f"{api_base}/user/convertSign", headers=headers, params={'convert_num': flow_val})
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
