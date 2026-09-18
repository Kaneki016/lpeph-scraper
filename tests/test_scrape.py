from lpeph_scraper import extract_emails, registration_no, scrape_firms
from lpeph_scraper.scrape import read_rows


class FakeClient:
    def __init__(self, firms, info):
        self.firms, self.info, self.calls = firms, info, []

    def search_firms(self):
        return self.firms

    def firm_info(self, code):
        self.calls.append(code)
        return self.info.get(code)


def test_registration_no():
    assert registration_no("3M REALTORS (E (3) 0485-2)") == "E (3) 0485-2"
    assert registration_no("NO REG") is None
    assert registration_no(None) is None


def test_scrape_resumes_and_reports_failures(tmp_path):
    out = str(tmp_path / "firms.csv")
    firms = [{"code": 1, "label": "A (R1)"}, {"code": 2, "label": "B (R2)"}]
    info = {1: {"firm_name": "A", "firm_registration_no": "R1", "status_id": 7, "email_address": "a@x.my"}}

    total, failed = scrape_firms(FakeClient(firms, info), out, workers=1)
    assert (total, failed) == (1, [2])

    info[2] = {"firm_name": "B", "firm_registration_no": "R2", "status_id": 7, "pic_email": "B@Y.MY"}
    client = FakeClient(firms, info)
    total, failed = scrape_firms(client, out, workers=1)
    assert (total, failed, client.calls) == (2, [], [2])
    assert [r["firm_code"] for r in read_rows(out)] == ["1", "2"]

    emails_out = tmp_path / "emails.txt"
    assert extract_emails(out, str(emails_out)) == 2
    assert emails_out.read_text().split() == ["a@x.my", "b@y.my"]
