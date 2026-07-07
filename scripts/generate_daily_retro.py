import argparse
import datetime as dt
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "daily_metrics"
RETRO_DIR = ROOT / "retros"


def yesterday_in_china() -> str:
    china_today = dt.datetime.utcnow() + dt.timedelta(hours=8)
    return (china_today.date() - dt.timedelta(days=1)).isoformat()


def rate_article(article: dict) -> str:
    views = int(article.get("views") or 0)
    shares = int(article.get("shares") or 0)
    likes = int(article.get("likes") or 0)
    favorites = int(article.get("favorites") or 0)

    share_rate = shares / views if views else 0
    like_rate = likes / views if views else 0
    fav_rate = favorites / views if views else 0

    if views >= 300 or share_rate >= 0.03:
        return "值得延展"
    if views >= 120 or share_rate >= 0.015 or like_rate >= 0.02 or fav_rate >= 0.01:
        return "可继续观察"
    return "需要调整"


def render_retro(metrics: dict) -> str:
    date_text = metrics["date"]
    lines = [
        f"# Daily Retro: {date_text}",
        "",
        "## 数据",
        "",
        f"- source: {metrics.get('source', 'unknown')}",
        f"- articles: {len(metrics.get('articles', []))}",
        "",
    ]

    for index, article in enumerate(metrics.get("articles", []), start=1):
        views = int(article.get("views") or 0)
        shares = int(article.get("shares") or 0)
        likes = int(article.get("likes") or 0)
        favorites = int(article.get("favorites") or 0)
        comments = int(article.get("comments") or 0)
        share_rate = shares / views if views else 0
        like_rate = likes / views if views else 0

        lines.extend(
            [
                f"### {index}. {article.get('title', '未命名文章')}",
                "",
                f"- 阅读: {views}",
                f"- 点赞: {likes}",
                f"- 转发: {shares}",
                f"- 收藏: {favorites}",
                f"- 评论: {comments}",
                f"- 转发率: {share_rate:.2%}" if views else "- 转发率: N/A",
                f"- 点赞率: {like_rate:.2%}" if views else "- 点赞率: N/A",
                f"- 初步判断: {rate_article(article)}",
                f"- 备注: {article.get('notes', '')}",
                "",
            ]
        )

    lines.extend(
        [
            "## 交给 Agent 的复盘任务",
            "",
            "请按「半生以后清醒课」的账号定位复盘昨天的数据：",
            "",
            "1. 判断每篇文章是标题问题、选题问题，还是正文问题。",
            "2. 分析哪些主题可以继续做系列。",
            "3. 给出下一篇最值得写的 5 个选题。",
            "4. 如果需要更新标题规则或选题规则，请给出具体修改建议。",
            "",
            "输出格式：",
            "",
            "```text",
            "这篇表现：",
            "可能原因：",
            "标题问题：",
            "选题问题：",
            "正文问题：",
            "下次改法：",
            "可延展选题：",
            "```",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=yesterday_in_china(), help="YYYY-MM-DD")
    parser.add_argument("--input", help="Metrics JSON path. Defaults to data/daily_metrics/<date>.json")
    args = parser.parse_args()

    input_path = Path(args.input) if args.input else DATA_DIR / f"{args.date}.json"
    if not input_path.is_absolute():
        input_path = ROOT / input_path
    if not input_path.exists():
        raise FileNotFoundError(f"Missing metrics file: {input_path}")

    metrics = json.loads(input_path.read_text(encoding="utf-8"))
    RETRO_DIR.mkdir(parents=True, exist_ok=True)
    output_path = RETRO_DIR / f"{args.date}.md"
    output_path.write_text(render_retro(metrics), encoding="utf-8")
    print(f"Wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
