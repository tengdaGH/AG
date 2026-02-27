# Calendar Sync 运维备忘 (Direct ICS 版)

## 🛠 同步原理
目前系统不再依赖 Google Calendar，而是直接抓取 iCloud 原始链接：
- Miya, Rita, 月月, 达哥的课表均通过 `sync_ics_to_notion.py` 同步。

## ⚠️ NOTION_TOKEN 会过期
**症状**：Notion 课表长时间未更新，即使 GitHub Actions 显示绿色 ✅
**排查方法**：去 GitHub Actions → 最近一次 run 的日志里搜索 `401`
**修复步骤**：
1. [notion.so/my-integrations](https://www.notion.so/my-integrations) → 找到 integration → 复制新 token
2. [GitHub Secrets](https://github.com/tengdaGH/AG/settings/secrets/actions) → `NOTION_TOKEN` → Update secret

## 🔗 原始链接备忘
如果需要更换老师或更新链接，请修改 `calendar_integration/sync_ics_to_notion.py` 中的 `ICS_FEEDS` 字典。

> 迁移日期：2026-02-27 (已解决 Google Calendar 同步延迟问题)

