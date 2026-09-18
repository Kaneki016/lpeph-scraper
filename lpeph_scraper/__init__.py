"""Scraper for the LPPEH (Malaysia) Business Information System firm registry."""

from .client import LpephClient, registration_no
from .scrape import extract_emails, scrape_firms

__all__ = ["LpephClient", "registration_no", "scrape_firms", "extract_emails"]
__version__ = "0.1.0"
