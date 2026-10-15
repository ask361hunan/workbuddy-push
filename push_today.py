# -*- coding: utf-8 -*-
"""
日常事务推送器 v2.0 —— 数据文件驱动版
- 每天 8:00 自动推送今日提醒到微信
- 提醒内容从 tasks.txt 读取（改 txt 即可，不用碰代码）
- Token 从环境变量 PUSHPLUS_TOKEN 或本地 pushplus_config.json 读取
"""
import os, json, sys, requests
from datetime import datetime, date

ROOT = os.path.dirname(os.path.abspath(__file__))
TASKS_FILE = os.path.join(ROOT, "tasks.txt")
CONFIG = os.path.join(ROOT, "pushplus_config.json")
API_URL = "http://www.pushplus.plus/send"

WEEKDAY_CN = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]


def load_tasks():
    """从 tasks.txt 读取提醒，返回 4 个列表"""
    daily, weekly, monthly, nodes = [], [], [], []
    if not os.path.exists(TASKS_FILE):
        return daily, weekly, monthly, nodes
    with open(TASKS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("|")
            if len(parts) < 3:
                continue
            kind = parts[0].strip()
            if kind == "每天" and len(parts) >= 3:
                daily.append((parts[1].strip(), parts[2].strip()))
            elif kind == "每周" and len(parts) >= 4:
                try:
                    weekly.append((int(parts[1]), parts[2].strip(), parts[3].strip()))
                except ValueError:
                    pass
            elif kind == "每月" and len(parts) >= 4:
                try:
                    monthly.append((int(parts[1]), parts[2].strip(), parts[3].strip()))
                except ValueError:
                    pass
            elif kind == "节点" and len(parts) >= 3:
                note = parts[3].strip() if len(parts) >= 4 else ""
                nodes.append((parts[1].strip(), parts[2].strip(), note))
    return daily, weekly, monthly, nodes


def build_today():
    daily, weekly, monthly, nodes = load_tasks()

    today = date.today()
    today_str = today.strftime("%Y-%m-%d")
    weekday = today.weekday()  # 0=周一
    cn = WEEKDAY_CN[weekday]

    lines = [f"📅 **今天 {today_str} · {cn}**\n", "---\n"]

    if daily:
        lines.append("**🔴 每日必做**\n")
        for t, txt in daily:
            lines.append(f"- `{t}` {txt}")
        lines.append("")

    today_weekly = [w for w in weekly if w[0] == weekday + 1]
    if today_weekly:
        lines.append(f"**🟡 今日 {cn}专属**\n")
        for _, t, txt in today_weekly:
            lines.append(f"- `{t}` {txt}")
        lines.append("")

    today_monthly = [m for m in monthly if m[0] == today.day]
    if today_monthly:
        lines.append(f"**🔴 本月 {today.day} 日专属**\n")
        for _, t, txt in today_monthly:
            lines.append(f"- `{t}` {txt}")
        lines.append("")

    today_nodes = [n for n in nodes if n[0] == today_str]
    if today_nodes:
        lines.append("**🚨🚨🚨 关键节点 🚨🚨🚨**\n")
        for _, title, note in today_nodes:
            lines.append(f"- ⭐ **{title}**")
            if note:
                lines.append(f"  > {note}")
        lines.append("")

    # 11 月生死月（动态倒计时）
    if "2026-11-01" <= today_str <= "2026-11-30":
        days_left = (date(2026, 11, 30) - today).days
        lines.append(f"**⚠️ 11 月生死月（还剩 {days_left} 天）**\n")
        lines.append("- □ 新公司注册（11/30 前拿执照）")
        lines.append("- □ 5 人名单成文")
        lines.append("- □ 给 1 人发消息预告\n")

    # 12 月第一单（动态倒计时）
    if "2026-12-01" <= today_str <= "2026-12-25":
        days_left = (date(2026, 12, 25) - today).days
        if days_left > 0:
            lines.append(f"**🎁 12 月第一单交付（还剩 {days_left} 天）**\n")
            lines.append("- 客户：免费/熟人价做「团队诊断 + 1 套改进方案」")
            lines.append("- 目标：1 单交付完，客户给评价\n")

    if not (daily or today_weekly or today_monthly or today_nodes):
        lines.append("🎈 今天没有额外提醒，按节奏推进主线即可。\n")

    lines.append("---")
    lines.append("📂 完整版：`D:\\我的知识库\\02-领域\\日常事务库.md`")
    lines.append("📱 卡片：`C:\\Users\\Administrator\\Desktop\\日常事务卡片.html`")
    lines.append("🔔 由 WorkBuddy 自动推送")

    title = f"📅 {today_str} {cn} · 今日提醒"
    return title, "\n".join(lines)


def load_token():
    env_token = os.environ.get("PUSHPLUS_TOKEN", "").strip()
    if env_token:
        return env_token
    if os.path.exists(CONFIG):
        try:
            with open(CONFIG, "r", encoding="utf-8") as f:
                return json.load(f).get("token", "").strip()
        except Exception:
            return None
    return None


def save_token(token):
    cfg = {"token": token, "created": datetime.now().strftime("%Y-%m-%d %H:%M")}
    with open(CONFIG, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def push(title, content, token):
    data = {"token": token, "title": title, "content": content, "template": "markdown"}
    try:
        r = requests.post(API_URL, json=data, timeout=15)
        return r.json()
    except Exception as e:
        return {"code": -1, "msg": f"网络错误: {e}"}


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "today"

    if arg == "save" and len(sys.argv) > 2:
        save_token(sys.argv[2])
        print(f"✅ Token 已保存到 {CONFIG}")
        sys.exit(0)

    if arg == "test":
        token = load_token() or (sys.argv[2] if len(sys.argv) > 2 else None)
        if not token:
            print("❌ 没有 token")
            sys.exit(1)
        result = push("🧪 测试推送", "PushPlus 通道正常 ✅", token)
        print(f"结果: {result}")
        sys.exit(0 if result.get("code") == 200 else 1)

    token = load_token()
    if not token:
        print("❌ 未找到 token，请先: push_today.py save <token>")
        sys.exit(1)

    title, content = build_today()
    result = push(title, content, token)
    print(f"推送结果: code={result.get('code')} msg={result.get('msg')}")
    if result.get("code") == 200:
        print("✅ 微信应已收到")
