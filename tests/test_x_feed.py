"""Offline regression tests for US-focused X RSS editorial selection."""
import importlib.util
from pathlib import Path
import unittest
from datetime import datetime, timezone


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "build_x_feed.py"
spec = importlib.util.spec_from_file_location("newstrendus_x_feed", SCRIPT)
x = importlib.util.module_from_spec(spec)
spec.loader.exec_module(x)


class XFeedTests(unittest.TestCase):
    def test_specific_hashtags_only(self):
        title = x.tweet_headline({
            "title": "Oregon drought forces ranchers to buy more cattle feed",
            "category": "US",
        })
        self.assertIn("#Oregon", title)
        self.assertIn("#Drought", title)
        self.assertEqual(title.count("#"), 2)

    def test_unrelated_country_headline_is_not_us(self):
        self.assertIsNone(x.US_SIGNALS.search(
            "Soldiers guard Milan during protests in Italy and France"
        ))
        self.assertIsNotNone(x.US_SIGNALS.search(
            "Federal Reserve rates debated in Wisconsin"
        ))

    def test_duplicate_topics(self):
        old = [{"title": "Oregon drought hits farmers as diesel costs rise"}]
        self.assertTrue(x.is_duplicate_topic(
            "Oregon drought hits farmers as diesel costs increase", old
        ))
        self.assertFalse(x.is_duplicate_topic(
            "NASA prepares another Moon mission", old
        ))

    def test_recent_us_news_outscores_older_non_us_world(self):
        now = datetime(2026, 10, 25, 16, 0, tzinfo=timezone.utc)
        local = {
            "title": "Oregon ranchers struggle with drought",
            "category": "US", "source": "npr.org",
            "date": "2026-10-25T14:00:00+00:00",
            "summary": "Farmers across Oregon are responding to drought and high feed costs.",
        }
        overseas = {
            "title": "Politics in a European country",
            "category": "World", "source": "bbc.co.uk",
            "date": "2026-10-25T15:30:00+00:00",
            "summary": "A debate in Europe without any United States connection.",
        }
        self.assertGreater(x.editorial_score(local, now, []),
                           x.editorial_score(overseas, now, []))

    def test_only_our_landing_page_link(self):
        link = x.attributed_share_link({
            "share_url": "https://newstrendus.com/social/stories/0123456789abcdef.html"
        })
        self.assertIn("utm_source=x", link)
        with self.assertRaises(ValueError):
            x.attributed_share_link({"share_url": "https://evil.example/news"})


if __name__ == "__main__":
    unittest.main()
