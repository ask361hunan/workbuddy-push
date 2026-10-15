# -*- coding: utf-8 -*-
"""
日常事务推送器 v1.0
- 每天 8 点自动推送今日提醒到微信
- 基于 02-领域/日常事务库.md 的 5 层时间表
- Token 从 config.json 读取（不硬编码）
"""
import os, json, sys, requests
from datetime import datetime, date

ROOT = r"C:/Users/Administrator/WorkBuddy/2026-10-12-05-20-54"
CONFIG = os.path.join(ROOT, "pushplus_config.json")
API_URL = "http://www.pushplus.plus/send"

# ============ 5 层时间表（与 02-领域/日常事务库.md 同步）============
DAILY = [
    ("08:00", "💰 看今日还款提醒（信用卡 App）"),
    ("08:10", "📰 看 1 条业务新闻（行业群/朋友圈）"),
    ("08:25", "📝 写今日 3 件事（必做1+重要1+推进1）"),
    ("22:30", "🌙 4-7-8 呼吸 + 关闭手机"),
]

WEEKLY = {
    0: [("21:00", "💑 周一 · 跟老婆过 5 分钟上周账单")],  # 周一
    2: [
        ("20:00", "🤝 周三 · 跟易鸣沟通聊天+工作想法"),
        ("20:30", "📞 周三 · 给老家父母做视频通话"),
    ],
    4: [("21:00", "📒 周五 · 周末账 15 分钟（与老婆）")],  # 周五
    5: [("全天", "👨‍👦 周六 · 不工作日（专门陪孩子）")],  # 周六
    6: [("21:00", "🔍 周日 · 每周复盘 30 分钟（对照 5 月方案 v3）")],  # 周日
}

MONTHLY = {
    1: [
        ("09:00", "💳 月初 · 房贷利息 2100 扣款确认"),
        ("09:10", "💳 月初 · 信用贷利息 1500 扣款确认"),
        ("09:30", "📊 月初 · 填 4 张表（收入+支出）"),
    ],
    30: [("21:00", "📅 月底 · 月复盘（对照个人档案）")],
}

# 关键节点
KEY_DATES = {
    "2026-10-20": ("🚨 协议发出去（黄老师）", "11 月生死月第 1 件"),
    "2026-10-25": ("🏢 启动新公司注册", "11/30 前拿执照"),
    "2026-10-30": ("💰 还信用卡 5 万", "11 月生死月第 3 件"),
    "2026-11-05": ("📋 5 人潜在客户名单成文", "11 月生死月第 4 件"),
    "2026-11-08": ("📤 给 1 人发消息预告", "11 月生死月第 5 件"),
    "2026-11-15": ("🔍 上半月复盘", "对照档案检查进度"),
    "2026-11-30": ("🎯 11 月复盘 + 生死月截止", "5 件事做了几件？"),
    "2026-12-01": ("🚀 启动 12 月第一单", "免费/熟人价团队诊断"),
    "2026-12-25": ("🎁 第一单交付", "12/31 前完成"),
    "2026-12-31": ("📊 2026 年终复盘", "暂缓清单砍掉 50%"),
    "2027-01-01": ("📱 启动朋友圈私域", "每周 1 条（2027 年开始）"),
}


def build_today():
    today = date.today()
    today_str = today.strftime("%Y-%m-%d")
    weekday = today.weekday()
    weekday_cn = ["一", "二", "三", "四", "五", "六", "日"][weekday]
    cn = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][weekday]

    lines = []
    lines.append(f"📅 **今天 {today_str} · {cn}**\n")
    lines.append("---\n")

    # 每日固定
    lines.append("**🔴 每日必做**\n")
    for t, txt in DAILY:
        lines.append(f"- `{t}` {txt}")
    lines.append("")

    # 本周特殊
    if weekday in WEEKLY:
        lines.append(f"**🟡 今日 {cn}专属**\n")
        for t, txt in WEEKLY[weekday]:
            lines.append(f"- `{t}` {txt}")
        lines.append("")

    # 本月
    if today.day in MONTHLY:
        lines.append(f"**🔴 本月 {today.day} 日专属**\n")
        for t, txt in MONTHLY[today.day]:
            lines.append(f"- `{t}` {txt}")
        lines.append("")

    # 关键节点
    if today_str in KEY_DATES:
        title, note = KEY_DATES[today_str]
        lines.append("**🚨🚨🚨 关键节点 🚨🚨🚨**\n")
        lines.append(f"- ⭐ **{title}**")
        lines.append(f"  > {note}\n")

    # 11 月生死月（每晚提醒，从 11/1 开始）
    if "2026-11-01" <= today_str <= "2026-11-30":
        import datetime
        d_end = date(2026, 11, 30)
        days_left = (d_end - today).days
        lines.append(f"**⚠️ 11 月生死月（还剩 {days_left} 天）**\n")
        lines.append("- □ 协议发出去（已改完）")
        lines.append("- □ 新公司注册（11/30 前拿执照）")
        lines.append("- □ 还信用卡 5 万")
        lines.append("- □ 5 人名单成文")
        lines.append("- □ 给 1 人发消息预告\n")

    # 12 月第一单
    if "2026-12-01" <= today_str <= "2026-12-25":
        import datetime
        d_end = date(2026, 12, 25)
        days_left = (d_end - today).days
        if days_left > 0:
            lines.append(f"**🎁 12 月第一单交付（还剩 {days_left} 天）**\n")
            lines.append("- 客户：免费/熟人价做「团队诊断 + 1 套改进方案」")
            lines.append("- 目标：1 单交付完，客户给评价\n")

    lines.append("---")
    lines.append("📂 完整版：`D:\\我的知识库\\02-领域\\日常事务库.md`")
    lines.append("📱 卡片：`C:\\Users\\Administrator\\Desktop\\日常事务卡片.html`")
    lines.append("🔔 由 WorkBuddy 自动推送")

    title = f"📅 {today_str} 周{weekday_cn} · 今日提醒"
    return title, "\n".join(lines)


def load_token():
    # 优先：环境变量（GitHub Actions / Linux 服务用这个）
    env_token = os.environ.get("PUSHPLUS_TOKEN", "").strip()
    if env_token:
        return env_token
    # 备选：本地配置文件
    if not os.path.exists(CONFIG):
        return None
    try:
        with open(CONFIG, "r", encoding="utf-8") as f:
            return json.load(f).get("token", "").strip()
    except Exception:
        return None


def save_token(token):
    cfg = {"token": token, "created": datetime.now().strftime("%Y-%m-%d %H:%M")}
    with open(CONFIG, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def push(title, content, token):
    data = {
        "token": token,
        "title": title,
        "content": content,
        "template": "markdown",
    }
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
        # 测试推送
        token = load_token() or (sys.argv[2] if len(sys.argv) > 2 else None)
        if not token:
            print("❌ 没有 token")
            sys.exit(1)
        title = "🧪 测试推送"
        content = "如果你看到这条消息，说明 PushPlus 通道已通。\n\n**WorkBuddy 推送系统就绪** ✅"
        result = push(title, content, token)
        print(f"结果: {result}")
        sys.exit(0 if result.get("code") == 200 else 1)

    # 默认：今日提醒
    token = load_token()
    if not token:
        print("❌ 未找到 token，请先: push_today.py save <你的token>")
        sys.exit(1)

    title, content = build_today()
    result = push(title, content, token)
    print(f"推送结果: code={result.get('code')} msg={result.get('msg')}")
    if result.get("code") == 200:
        print("✅ 微信应已收到（关注「推送加」公众号）")
