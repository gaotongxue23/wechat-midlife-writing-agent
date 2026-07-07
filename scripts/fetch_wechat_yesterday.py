import argparse
import datetime as dt
import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "daily_metrics"


def request_json(url: str, payload: dict | None = None) -> dict:
    data = None
    headers = {"User-Agent": "wechat-midlife-writing-agent/0.1"}
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def get_access_token(appid: str, secret: str) -> str:
    query = urllib.parse.urlencode(
        {
            "grant_type": "client_credential",
            "appid": appid,
            "secret": secret,
        }
    )
    result = request_json(f"https://api.weixin.qq.com/cgi-bin/token?{query}")
    if "access_token" not in result:
        raise RuntimeError(f"Failed to get access_token: {result}")
    return result["access_token"]


def fetch_article_summary(access_token: str, date_text: str) -> dict:
    url = (
        "https://api.weixin.qq.com/datacube/getarticlesummary"
        f"?access_token={urllib.parse.quote(access_token)}"
    )
    payload = {
        "begin_date": date_text,
        "end_date": date_text,
    }
    return request_json(url, payload)


def normalize_wechat_summary(date_text: str, raw: dict) -> dict:
    articles = []
    for item in raw.get("list", []):
        articles.append(
            {
                "title": item.get("title", ""),
                "url": "",
                "published_at": f"{date_text}T00:00:00+08:00",
                "views": item.get("int_page_read_user", 0),
                "likes": item.get("add_to_fav_user", 0),
                "shares": item.get("share_user", 0),
                "favorites": item.get("add_to_fav_user", 0),
                "comments": 0,
                "new_followers": 0,
                "notes": "Fetched from WeChat datacube/getarticlesummary.",
                "raw": item,
            }
        )
    return {
        "date": date_text,
        "source": "wechat_datacube_getarticlesummary",
        "articles": articles,
        "raw": raw,
    }


def yesterday_in_china() -> str:
    # WeChat official account data is usually interpreted by China Standard Time.
    china_today = dt.datetime.utcnow() + dt.timedelta(hours=8)
    return (china_today.date() - dt.timedelta(days=1)).isoformat()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=yesterday_in_china(), help="YYYY-MM-DD")
    args = parser.parse_args()

    appid = os.getenv("WECHAT_APPID")
    secret = os.getenv("WECHAT_APPSECRET")
    if not appid or not secret:
        print("Missing WECHAT_APPID or WECHAT_APPSECRET.", file=sys.stderr)
        return 2

    token = get_access_token(appid, secret)
    raw = fetch_article_summary(token, args.date)
    if raw.get("errcode"):
        print(f"WeChat API returned an error: {raw}", file=sys.stderr)
        return 3

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    output = OUT_DIR / f"{args.date}.json"
    output.write_text(
        json.dumps(normalize_wechat_summary(args.date, raw), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

