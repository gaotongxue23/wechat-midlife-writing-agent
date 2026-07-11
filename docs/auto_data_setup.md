# 自动获取昨天数据

这套流程使用微信公众号官方 DataCube 接口，不需要打开后台浏览器。

每天 08:15 自动执行：

```text
微信公众号 DataCube → data/daily_metrics/YYYY-MM-DD.json → retros/YYYY-MM-DD.md
```

08:15 之后，09:00 的写作 Agent 直接读取复盘文件，再生成当天文章。

## 1. 配置官方凭据

在公众号后台的“基本配置”中取得 AppID 和 AppSecret。不要把它们写进项目文件或提交到 Git。

在 PowerShell 运行一次：

```powershell
[Environment]::SetEnvironmentVariable('WECHAT_APPID', '你的AppID', 'User')
[Environment]::SetEnvironmentVariable('WECHAT_APPSECRET', '你的AppSecret', 'User')
```

关闭并重新打开 PowerShell 或 Codex 后，环境变量才会出现在新进程中。

## 2. 测试配置

先只检查，不访问网络：

```powershell
python scripts/run_daily_retro.py --dry-run
```

确认两项凭据都是 `True` 后，手动跑一次指定日期：

```powershell
python scripts/run_daily_retro.py --date 2026-07-10
```

成功后会生成：

```text
data/daily_metrics/2026-07-10.json
retros/2026-07-10.md
logs/daily-retro.log
```

原始数据和日志默认不提交到 Git。

## 3. 注册 Windows 每日任务

确认手动测试成功后，运行：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/register_daily_task.ps1
```

它会创建名为 `WechatMidlifeDailyRetro` 的当前用户任务，每天 08:15 执行。

查看任务：

```powershell
Get-ScheduledTask -TaskName WechatMidlifeDailyRetro
```

删除任务：

```powershell
Unregister-ScheduledTask -TaskName WechatMidlifeDailyRetro -Confirm:$false
```

## 数据范围

- `getarticlesummary` 自动获取图文的阅读、转发、收藏、点赞等数据。
- `getusersummary` 自动获取账号当天的新增、取消和净增关注。
- 官方接口提供的是账号级新增关注，不能准确归因到单篇文章；“阅读后关注”等单篇转化仍需从后台内容分析页补充。
- 某些极低互动的图文可能不会出现在每日图文统计结果里，这是平台接口的统计限制，不是脚本故障。
