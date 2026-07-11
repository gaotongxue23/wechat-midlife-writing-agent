import argparse
import datetime as dt
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Optional


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "daily_metrics"
CHINA_TZ = dt.timezone(dt.timedelta(hours=8), name="CST")


class WeChatApiError(RuntimeError):
    """Raised when the WeChat DataCube API returns an error payload."""


def request_json(url: str, payload: Optional[dict] = None) -> dict:
    data = None
    headers = {"User-Agent": "wechat-midlife-writing-agent/0.2"}
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(url, data=data, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")[:500]
        raise WeChatApiError(f"WeChat HTTP {error.code}: {body}") from error
    except urllib.error.URLError as error:
        raise WeChatApiError(f"Unable to reach WeChat API: {error.reason}") from error


def check_api_error(result: dict, operation: str) -> dict:
    if result.get("errcode"):
        raise WeChatApiError(f"{operation} failed: {result}")
    return result


def get_access_token(appid: str, secret: str) -> str:
    query = urllib.parse.urlencode(
        {
            "grant_type": "client_credential",
            "appid": appid,
            "secret": secret,
        }
    )
    result = check_api_error(
        request_json(f"https://api.weixin.qq.com/cgi-bin/token?{query}"),
        "access token request",
    )
    token = result.get("access_token")
    if not token:
        raise WeChatApiError(f"Access token missing from response: {result}")
    return token


def post_datacube(access_token: str, endpoint: str, date_text: str) -> dict:
    url = f"https://api.weixin.qq.com/datacube/{endpoint}?access_token={urllib.parse.quote(access_token)}"
    return check_api_error(
        request_json(url, {"begin_date": date_text, "end_date": date_text}),
        endpoint,
    )


def fetch_article_summary(access_token: str, date_text: str) -> dict:
    return post_datacube(access_token, "getarticlesummary", date_text)


def fetch_user_summary(access_token: str, date_text: str) -> dict:
    return post_datacube(access_token, "getusersummary", date_text)


def value(item: dict, field: str) -> int:
    return int(item.get(field) or 0)


def normalize_wechat_summary(date_text: str, article_raw: dict, user_raw: Optional[dict]) -> dict:
    articles = []
    for item in article_raw.get("list", []):
        articles.append(
            {
                "title": item.get("title", ""),
                "url": "",
                "published_at": f"{date_text}T00:00:00+08:00",
                "stat_date": item.get("ref_date", date_text),
                "views": value(item, "int_page_read_user"),
                "page_reads": value(item, "int_page_read_count"),
                "original_page_views": value(item, "ori_page_read_user"),
                "likes": value(item, "like_count"),
                "shares": value(item, "share_user"),
                "share_count": value(item, "share_count"),
                "favorites": value(item, "add_to_fav_user"),
                "favorite_count": value(item, "add_to_fav_count"),
                "comments": value(item, "comment_count"),
                "new_followers": None,
                "notes": "Fetched from WeChat DataCube getarticlesummary. New followers are account-level and stored separately.",
                "raw": item,
            }
        )

    user_items = (user_raw or {}).get("list", [])
    account_metrics = {
        "new_users": sum(value(item, "new_user") for item in user_items),
        "cancel_users": sum(value(item, "cancel_user") for item in user_items),
        "net_new_users": sum(value(item, "new_user") - value(item, "cancel_user") for item in user_items),
        "notes": "Account-level follower changes from WeChat DataCube getusersummary; they are not attributable to a single article.",
    }

    return {
        "date": date_text,
        "source": "wechat_datacube",
        "articles": articles,
        "account_metrics": account_metrics,
        "raw": {
            "article_summary": article_raw,
            "user_summary": user_raw,
        },
    }


def yesterday_in_china() -> str:
    return (dt.datetime.now(CHINA_TZ).date() - dt.timedelta(days=1)).isoformat()


def fetch_and_write(date_text: str, output_path: Optional[Path] = None, include_user_summary: bool = True) -> Path:
    appid = os.getenv("WECHAT_APPID")
    secret = os.getenv("WECHAT_APPSECRET")
    if not appid or not secret:
        raise RuntimeError("Missing WECHAT_APPID or WECHAT_APPSECRET. Set them as user environment variables before running the fetcher.")

    token = get_access_token(appid, secret)
    article_raw = fetch_article_summary(token, date_text)
    user_raw = fetch_user_summary(token, date_text) if include_user_summary else None

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    destination = output_path or OUT_DIR / f"{date_text}.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(normalize_wechat_summary(date_text, article_raw, user_raw), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return destination


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch yesterday's WeChat Official Account DataCube metrics.")
    parser.add_argument("--date", default=yesterday_in_china(), help="Statistics date in YYYY-MM-DD format")
    parser.add_argument("--output", help="Optional output JSON path")
    parser.add_argument("--skip-user-summary", action="store_true", help="Skip account-level follower metrics")
    parser.add_argument("--dry-run", action="store_true", help="Validate local configuration without calling the API")
    args = parser.parse_args()

    try:
        dt.date.fromisoformat(args.date)
    except ValueError:
        print(f"Invalid --date: {args.date}. Expected YYYY-MM-DD.", file=sys.stderr)
        return 2

    if args.dry_run:
        output = Path(args.output) if args.output else OUT_DIR / f"{args.date}.json"
        print(f"Date: {args.date}")
        print(f"Output: {output}")
        print(f"WECHAT_APPID configured: {bool(os.getenv('WECHAT_APPID'))}")
        print(f"WECHAT_APPSECRET configured: {bool(os.getenv('WECHAT_APPSECRET'))}")
        return 0

    try:
        output = fetch_and_write(
            args.date,
            Path(args.output) if args.output else None,
            include_user_summary=not args.skip_user_summary,
        )
    except (RuntimeError, WeChatApiError) as error:
        print(error, file=sys.stderr)
        return 3

    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
