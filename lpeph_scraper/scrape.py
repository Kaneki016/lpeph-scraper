"""Scrape firm details into a CSV, resuming from any existing output."""

from __future__ import annotations

import csv
import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

from .client import LpephClient, registration_no

log = logging.getLogger(__name__)

DEFAULT_COLUMNS = [
    "firm_code", "firm_name", "firm_registration_no", "filtered_firm_type",
    "email_address", "email_address2", "pic_email",
    "tel_no", "mobile_no", "fax_no", "website",
    "business_state_id", "status_id",
]
EMAIL_COLUMNS = ("email_address", "email_address2", "pic_email")


def read_rows(path: str) -> list[dict]:
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8-sig", newline="") as fp:
        return list(csv.DictReader(fp))


def write_rows(path: str, rows: list[dict], columns: list[str]) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8-sig", newline="") as fp:
        w = csv.DictWriter(fp, fieldnames=columns, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def scrape_firms(client: LpephClient, out: str, workers: int = 4, limit: int | None = None,
                 resume: bool = True, all_fields: bool = False) -> tuple[int, list]:
    """Fetch details for every firm and write them to `out`.

    With resume=True, firms already present in `out` (matched by code or
    registration number) are skipped. Returns (rows written, failed codes).
    """
    existing = read_rows(out) if resume else []
    done_codes = {r.get("firm_code") for r in existing if r.get("firm_code")}
    done_regs = {r.get("firm_registration_no") for r in existing if r.get("firm_registration_no")}

    firms = client.search_firms()
    log.info("registry lists %d firms; %d already in %s", len(firms), len(existing), out)
    todo = [f for f in firms
            if str(f["code"]) not in done_codes and registration_no(f["label"]) not in done_regs]
    if limit:
        todo = todo[:limit]
    log.info("fetching %d firms with %d workers", len(todo), workers)

    new_rows, failed = [], []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = {ex.submit(client.firm_info, f["code"]): f for f in todo}
        for i, fut in enumerate(as_completed(futures), 1):
            firm = futures[fut]
            d = fut.result()
            if d:
                new_rows.append({"firm_code": firm["code"], **d})
            else:
                failed.append(firm["code"])
            if i % 250 == 0:
                log.info("processed %d/%d ok=%d failed=%d", i, len(todo), len(new_rows), len(failed))

    rows = existing + new_rows
    if all_fields:
        columns = list(DEFAULT_COLUMNS)
        for r in rows:
            columns += [k for k in r if k not in columns]
    else:
        columns = DEFAULT_COLUMNS
    write_rows(out, rows, columns)
    log.info("wrote %d rows (%d new), %d failed", len(rows), len(new_rows), len(failed))
    return len(rows), failed


def extract_emails(csv_path: str, out: str) -> int:
    """Write the sorted, de-duplicated, lower-cased email addresses found in `csv_path`."""
    emails = set()
    for r in read_rows(csv_path):
        for k in EMAIL_COLUMNS:
            v = (r.get(k) or "").strip()
            if "@" in v:
                emails.add(v.lower())
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    with open(out, "w", encoding="utf-8") as fp:
        fp.write("\n".join(sorted(emails)) + "\n")
    return len(emails)
