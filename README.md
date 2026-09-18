# lpeph-scraper

Scrapes the public firm registry of the **Lembaga Penilai, Pentaksir, Ejen Harta Tanah dan Pengurus Harta (LPPEH)**, Malaysia's Board of Valuers, Appraisers, Estate Agents and Property Managers, via the JSON API behind [bis.lpeph.gov.my/search](https://bis.lpeph.gov.my/search).

- Lists every registered firm (about 5,100)
- Fetches each firm's details (type, status, phone, email, website, state)
- Resumable: re-running only fetches firms missing from the output, so failed ones are retried
- Handles the API's flaky or partial responses with retries and validation

## Install

```bash
git clone https://github.com/Kaneki016/lpeph-scraper && cd lpeph-scraper
pip install -e .
```

Requires Python 3.9+.

## Usage

```bash
# fetch all firms -> data/firms.csv (re-run to retry failures)
lpeph-scraper firms

# try it on a few firms first
lpeph-scraper firms --limit 10 -o data/sample.csv

# extract unique email addresses from the CSV
lpeph-scraper emails -i data/firms.csv -o data/emails.txt
```

`python -m lpeph_scraper ...` works too.

| Option | Default | Notes |
|---|---|---|
| `-o, --out` | `data/firms.csv` | output CSV |
| `-w, --workers` | `4` | concurrent requests; keep this low |
| `--limit N` | – | only fetch N firms |
| `--fresh` | off | ignore existing output and refetch everything |
| `--all-fields` | off | keep all ~80 fields the API returns |
| `--verify-tls` | off | the site serves an incomplete cert chain, so verification fails on most machines |

The exit code is `1` if any firm failed, which makes retry loops easy to script.

### As a library

```python
from lpeph_scraper import LpephClient, scrape_firms

client = LpephClient()
firms = client.search_firms()            # [{'code': 1, 'label': '3L ENTERPRISES (AE (3) 0006)'}, ...]
details = client.firm_info(firms[0]["code"])
```

## API notes

| Endpoint | Method | Body | Returns |
|---|---|---|---|
| `/api/firm/search` | POST | `{}` | all firms `{code, label}` |
| `/api/firm/info` | POST | `{"firm_id": <code>}` | firm object (~80 keys) |

Under load, `firm/info` sometimes returns an empty or partial object with HTTP 200. The client treats a response as valid only if it has `firm_name` and `status_id`.

## Responsible use

- This tool only reads data that the registry publishes. You are responsible for how you use what it collects.
- Contact details can be **personal data** under Malaysia's Personal Data Protection Act 2010 (PDPA). Don't republish the data, and don't use it for unsolicited bulk marketing.
- Keep concurrency low. The site is a government service.
- Scraped output goes to `data/`, which is git-ignored. Don't commit it.

## Development

```bash
pip install -e ".[dev]"
pytest
```

## License

MIT
