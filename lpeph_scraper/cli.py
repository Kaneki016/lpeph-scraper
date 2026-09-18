"""Command-line entry point: `lpeph-scraper firms` / `lpeph-scraper emails`."""

from __future__ import annotations

import argparse
import logging
import sys

from .client import LpephClient
from .scrape import extract_emails, scrape_firms


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="lpeph-scraper",
                                description="Scrape the LPPEH (Malaysia) firm registry.")
    p.add_argument("-v", "--verbose", action="store_true")
    sub = p.add_subparsers(dest="cmd", required=True)

    f = sub.add_parser("firms", help="fetch firm details into a CSV (resumable)")
    f.add_argument("-o", "--out", default="data/firms.csv")
    f.add_argument("-w", "--workers", type=int, default=4, help="concurrent requests (be polite)")
    f.add_argument("--limit", type=int, help="only fetch N firms (for testing)")
    f.add_argument("--fresh", action="store_true", help="ignore existing output and refetch everything")
    f.add_argument("--all-fields", action="store_true", help="keep every field the API returns")
    f.add_argument("--verify-tls", action="store_true",
                   help="verify TLS certificates (fails unless your CA store has the site's intermediate)")

    e = sub.add_parser("emails", help="extract unique emails from a firms CSV")
    e.add_argument("-i", "--input", default="data/firms.csv")
    e.add_argument("-o", "--out", default="data/emails.txt")

    args = p.parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")

    if args.cmd == "firms":
        client = LpephClient(verify_tls=args.verify_tls)
        total, failed = scrape_firms(client, args.out, workers=args.workers, limit=args.limit,
                                     resume=not args.fresh, all_fields=args.all_fields)
        print(f"{total} firms in {args.out}; {len(failed)} failed (re-run to retry)")
        return 1 if failed else 0

    if args.cmd == "emails":
        n = extract_emails(args.input, args.out)
        print(f"{n} unique emails -> {args.out}")
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
