# WorkBuddy 日常推送

每天北京时间 8:00 自动推送"今日提醒"到微信（通过 PushPlus）。

**电脑关机也能用** —— GitHub Actions 云端执行。

## 文件结构

```
.
├── push_today.py          # 主推送脚本
├── requirements.txt       # 依赖
├── .github/workflows/
│   └── daily.yml          # Actions 配置（北京时间 8:00 触发）
└── README.md
```

## 配置步骤

1. **创建 PushPlus Token**：访问 https://www.pushplus.plus 注册并实名
2. **配置 GitHub Secret**：
   - 仓库 → Settings → Secrets and variables → Actions
   - 点 New repository secret
   - Name: `PUSHPLUS_TOKEN`
   - Value: 你的 PushPlus Token
3. **关注公众号**：微信关注「推送加」接收消息
4. **测试**：Actions 标签页 → 选择 "日常事务推送" → Run workflow

## 触发时间

- 自动：每天 UTC 0:00（北京时间 8:00）
- 手动：Actions 页面 → Run workflow

## 修改推送内容

编辑 `push_today.py` 里 DAILY/WEEKLY/MONTHLY/KEY_DATES 四个字典。
