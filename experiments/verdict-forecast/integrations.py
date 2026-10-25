"""Read-only fixed public metadata adapters. Never use data for automated truth claims."""
import json
import re
import urllib.request
import xml.etree.ElementTree as ET

SOURCES = {
    "macrovoices": ("https://feed.podbean.com/macrovoices/feed.xml", "rss"),
    "kalshi": ("https://external-api.kalshi.com/trade-api/v2/markets?limit=10&status=open", "json"),
    "polymarket": ("https://gamma-api.polymarket.com/markets?active=true&closed=false&limit=10", "json"),
    "bls": ("https://api.bls.gov/publicAPI/v1/timeseries/data/LNS14000000", "json"),
}


def fetch_fixed(service):
    """Only allow hard-coded destinations; callers must not supply arbitrary URLs."""
    if service not in SOURCES:
        raise ValueError("Unsupported source; URL input disabled to avoid SSRF")
    url, encoding = SOURCES[service]
    request = urllib.request.Request(url, headers={"User-Agent": "VerdictForecastPilot/0.8"})
    with urllib.request.urlopen(request, timeout=8) as response:
        if response.geturl().split('/')[2] != url.split('/')[2]:
            raise ValueError("Unexpected redirect host")
        payload = response.read(1500001)
        if len(payload) > 1500000:
            raise ValueError("Upstream response too large")
    return parse_metadata(service, payload)


def parse_metadata(service, payload):
    """Normalize a few public fields; never turn provider prices into verified probabilities."""
    if service == "macrovoices":
        root = ET.fromstring(payload)
        def txt(item, name):
            return (item.findtext(name) or "").strip()
        return [{"title": txt(i, "title"), "url": txt(i, "link"), "date": txt(i, "pubDate")}
                for i in root.findall(".//channel/item")[:10]]
    data = json.loads(payload)
    if service == "kalshi":
        return [{"title": m.get("title"), "ticker": m.get("ticker"), "yes_bid": m.get("yes_bid_dollars"), "yes_ask": m.get("yes_ask_dollars"), "close_time": m.get("close_time")}
                for m in data.get("markets", [])[:10]]
    if service == "polymarket":
        return [{"title": m.get("question"), "slug": m.get("slug"), "outcome_prices_raw": m.get("outcomePrices"), "end_date": m.get("endDate")}
                for m in data[:10]]
    if service == "bls":
        return [{"series_id": s.get("seriesID"), "observations": s.get("data", [])[:3]}
                for s in data.get("Results", {}).get("series", [])[:2]]
    raise ValueError("Unsupported parser")
