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
        "Accept-Language": "zh-CN,zh;q=0.9",
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
        
        if isinstance(login_data, dict) and login_data.get('data'):
            data_field = login_data['data']
            if isinstance(data_field, dict):
                for key in ['authorization', 'auth_data', 'token', 'access_token']:
                    val = data_field.get(key)
                    if val and isinstance(val, str) and val.startswith('ey'):
                        dynamic_token = val
                        break
                if not dynamic_token:
                    dynamic_token = data_field.get('authorization') or data_field.get('auth_data')
            elif isinstance(data_field, str): 
                dynamic_token = data_field

        if dynamic_token:
            print(f"✅ 登录成功，已精准获取真正 Token！(Token前缀: {dynamic_token[:15]}...)")
            
            headers['Authorization'] = dynamic_token
            headers['authorization'] = dynamic_token
            
            session.cookies.update({
                'auth_data': dynamic_token,
                'authorization': dynamic_token
            })
        else:
            print(f"❌ 提取真正 Token 失败！请看服务器到底返回了什么: {login_data}")
            return

        # ==========================================
        # 步骤二：执行每日签到
        # ==========================================
        print("🚀 开始执行签到任务...")
        time.sleep(2) 
        
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
        # 步骤三：查询剩余流量与抵消逻辑
        # ==========================================
        if res.status_code == 200 or (res.text and "已签到" in res.text):
            time.sleep(2) 
            print("🔄 正在获取您的签到流量数据...")
            
            list_res = session.get(f"{api_base}/user/getSignList", headers=headers, timeout=10)
            
            try:
                list_json = list_res.json()
                
                # --- 💡 新增：提取并计算当前剩余流量 ---
                total_traffic = float(list_json.get('total', 0))
                used_traffic = float(list_json.get('yishiyong_total', 0))
                remain_traffic = total_traffic - used_traffic
                
                print(f"💰 【签到流量池】累计获取: {total_traffic:.2f}GB | 已抵消: {used_traffic:.2f}GB | 当前剩余: {remain_traffic:.2f}GB")
                
                # 检查抵消开关
                if ENABLE_OFFSET.lower() != 'true':
                    print(f"🛑 自动抵消未开启 (当前设置: {ENABLE_OFFSET})，任务圆满结束。")
                    return

                print("⚙️ 抵消开关已开启，准备执行抵消...")
                list_data = list_json.get('data', [])
                if list_data and isinstance(list_data, list):
                    first_item = list_data[0]
                    flow_val = first_item.get('get_num')
                    
                    # 只有当剩余流量大于 0 时，才发起抵消请求
                    if flow_val and remain_traffic > 0: 
                        convert_res = session.get(f"{api_base}/user/convertSign", headers=headers, params={'convert_num': flow_val}, timeout=10)
                        print(f"🎁 抵消结果: {convert_res.json().get('message', '完成')}")
                    else:
                        print("ℹ️ 当前没有可抵消的剩余流量，或本次流量已抵消。")
                else:
                    print("ℹ️ 未查询到任何最新的流量记录。")
            except Exception as e:
                print(f"⚠️ 获取流量列表或抵消失败: {e}")

    except Exception as e:
        print(f"💥 运行出错，异常信息: {str(e)}")

if __name__ == "__main__":
    run_task()
