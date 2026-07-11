import argparse
import datetime as dt
import sys
from pathlib import Path

import fetch_wechat_yesterday
import generate_daily_retro


ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = ROOT / "logs"


def log(message: str) -> None:
    timestamp = dt.datetime.now().astimezone().isoformat(timespec="seconds")
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with (LOG_DIR / "daily-retro.log").open("a", encoding="utf-8") as handle:
        handle.write(f"{timestamp} {message}\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch WeChat metrics and create the daily retro in one command.")
    parser.add_argument("--date", default=fetch_wechat_yesterday.yesterday_in_china(), help="Statistics date in YYYY-MM-DD format")
    parser.add_argument("--dry-run", action="store_true", help="Validate the planned run without calling WeChat")
    args = parser.parse_args()

    if args.dry_run:
        print(f"Would fetch WeChat metrics for {args.date} and write a retro report.")
        print(f"WECHAT_APPID configured: {bool(fetch_wechat_yesterday.os.getenv('WECHAT_APPID'))}")
        print(f"WECHAT_APPSECRET configured: {bool(fetch_wechat_yesterday.os.getenv('WECHAT_APPSECRET'))}")
        return 0

    try:
        metrics_path = fetch_wechat_yesterday.fetch_and_write(args.date)
        retro_path = generate_daily_retro.generate_and_write(metrics_path)
    except Exception as error:
        log(f"FAILED date={args.date} error={error}")
        print(f"Daily retro failed: {error}", file=sys.stderr)
        return 1

    log(f"OK date={args.date} metrics={metrics_path.name} retro={retro_path.name}")
    print(f"Metrics: {metrics_path}")
    print(f"Retro: {retro_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
