# Daily Retro Workflow

目标：每天获取“昨天”的公众号数据，并让 Agent 复盘。

## 路线 A：先手动录入，今天就能用

在公众号后台查看昨天发布内容的数据，然后新建：

```text
data/daily_metrics/YYYY-MM-DD.json
```

格式参考：

```json
{
  "date": "2026-07-06",
  "source": "manual",
  "articles": [
    {
      "title": "夫妻到了晚年，最怕的不是吵架，而是无话可说",
      "url": "",
      "published_at": "2026-07-06T08:00:00+08:00",
      "views": 123,
      "average_read_duration_minutes": 1.73,
      "completion_rate": 0.22,
      "likes": 2,
      "shares": 2,
      "favorites": 1,
      "comments": 0,
      "new_followers": 0,
      "notes": ""
    }
  ]
}
```

然后运行：

```bash
python scripts/generate_daily_retro.py --date 2026-07-06
```

脚本会生成：

```text
retros/2026-07-06.md
```

把这个文件内容发给 Agent，它就能按账号规则复盘。

## 路线 B：接微信公众号图文分析接口

如果你的公众号具备开发者权限，可以用微信的图文分析数据接口拉取数据。

需要准备环境变量：

```bash
WECHAT_APPID=你的AppID
WECHAT_APPSECRET=你的AppSecret
```

然后运行：

```bash
python scripts/fetch_wechat_yesterday.py
python scripts/generate_daily_retro.py
```

注意：

- 微信接口权限、账号类型、IP 白名单和数据延迟都会影响是否能拉取成功。
- 如果接口暂时不可用，就继续用路线 A 手动录入。
- 原始数据文件默认不会提交到 Git，因为可能包含账号运营数据。
- 每天优先记录新增关注、完成率和平均阅读时长；只有阅读量无法判断文章是否真的带来增长。
