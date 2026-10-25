import importlib.util
import pathlib
import unittest
from unittest.mock import patch

path = pathlib.Path(__file__).with_name("integrations.py")
spec = importlib.util.spec_from_file_location("vf_integrations", path)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class AdaptersTest(unittest.TestCase):
    def test_known_hosts_only(self):
        with self.assertRaises(ValueError):mod.fetch_fixed("http://169.254.169.254/latest")
    def test_rss(self):
        xml = b"<rss><channel><item><title>E1</title><pubDate>Today</pubDate></item></channel></rss>"
        self.assertEqual(mod.parse_metadata("macrovoices", xml)[0]["title"], "E1")
    def test_kalshi(self):
        self.assertEqual(mod.parse_metadata("kalshi", b'{"markets":[{"ticker":"T1","yes_bid_dollars":"0.40"}]}')[0]["ticker"], "T1")
    def test_polymarket(self):
        self.assertEqual(mod.parse_metadata("polymarket", b'[{"question":"Example"}]')[0]["title"], "Example")
    def test_bls(self):
        self.assertEqual(mod.parse_metadata("bls", b'{"Results":{"series":[{"seriesID":"LNS14000000"}]}}')[0]["series_id"], "LNS14000000")

if __name__ == "__main__":unittest.main()
