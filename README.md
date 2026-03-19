# 🐰 淘气兔全自动签到与抵消脚本 (Taoqitu Auto Checkin)

本项目是一个基于 Python 和 GitHub Actions 构建的自动化工具，专门用于「淘气兔 (Taoqitu)」平台的每日自动签到以及流量抵消。

得益于**动态账号密码登录**机制，本脚本完美解决了传统固定 Token 容易过期的问题，真正做到了一劳永逸的“无人值守”运行。

---

## ✨ 核心功能

* **🔐 动态鉴权登录**：自动模拟浏览器行为，绕过基础防护，通过账号密码动态获取最新的 JWT Token。
* **📅 每日自动签到**：依托 GitHub Actions，每天定时（默认北京时间 08:30）自动执行签到，绝不漏签。
* **🎁 智能流量抵消**：内置开关。开启后，会在签到成功时自动查询并提取未转换的流量记录，执行抵消操作。
* **🧹 日志自动清理**：每次运行结束后，自动调用 GitHub CLI 清理旧的 Action 运行日志，保持仓库整洁。

---

## 🚀 快速开始

只需简单的几步，即可将本脚本部署到你自己的 GitHub 仓库中长期运行。

### 第一步：准备仓库
1. 点击右上角的 `Fork` 按钮，将本项目复制到你自己的 GitHub 账号下。
2. 进入你 Fork 后的仓库，点击顶部菜单栏的 **Actions**。
3. 如果看到一条提示 "I understand my workflows, go ahead and enable them"，请点击确认，启用 Actions 功能。

### 第二步：配置账号密码 (Secrets)
为了安全起见，绝对不要将账号密码写在代码中。请使用 GitHub Secrets 进行配置：

1. 在你的仓库中，依次点击 **Settings** -> **Secrets and variables** -> **Actions**。
2. 点击绿色的 **New repository secret** 按钮，分别添加以下三个变量：

| 变量名 (Name) | 填写说明 (Secret) | 是否必填 |
| :--- | :--- | :--- |
| `USERNAME` | 你的淘气兔登录邮箱帐号 (如 `test@gmail.com`) | **必填** |
| `PASSWORD` | 你的淘气兔登录密码 | **必填** |
| `ENABLE_OFFSET` | 是否开启流量抵消。填 `true` 开启，填 `false` (或不填) 关闭。 | 选填 |

### 第三步：赋予 Actions 读写权限
为了让“日志自动清理”功能正常工作，需要确保 Actions 拥有写入权限：
1. 在仓库的 **Settings** 中，点击左侧导航栏的 **Actions** -> **General**。
2. 滚动到底部的 **Workflow permissions** 区域。
3. 勾选 **Read and write permissions**，然后点击 **Save**。

### 第四步：手动触发测试
1. 点击仓库顶部的 **Actions** 标签。
2. 在左侧列表中选择 **Taoqitu Auto Checkin**。
3. 点击右侧的 **Run workflow** 按钮，手动执行一次。
4. 等待片刻，如果看到绿色的 `✓`，并且点开日志能看到 `🎉 签到反馈`，则说明配置完全成功！

---

## ⚙️ 自定义执行时间

默认的执行时间是每天北京时间 08:30。如果你想修改执行时间，请编辑 `.github/workflows/checkin.yml` 文件中的 `cron` 表达式：

```yaml
on:
  schedule:
    # 这里的触发时间是 UTC 时间。
    # 例如：UTC 的 00:30，对应北京时间 (UTC+8) 的 08:30
    - cron: '30 0 * * *'
