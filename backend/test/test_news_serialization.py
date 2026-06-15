import unittest
from datetime import date
from types import SimpleNamespace

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.v1.endpoints.news import _serialize_news, list_news
from app.db.session import Base
from app.models.news import News


def _news_row(**overrides):
    values = {
        "id": 1,
        "external_id": "news-1",
        "category": "RECENT_NEWS",
        "title": "Test news",
        "content": "Body",
        "url": None,
        "keywords": None,
        "media": "Test media",
        "country": "KOR",
        "region": "South Korea",
        "published_at": None,
        "created_at": None,
        "esg_score": None,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


class NewsSerializationTests(unittest.TestCase):
    def test_explicit_url_is_returned(self):
        result = _serialize_news(
            _news_row(
                content="Article body",
                url="https://example.com/article",
            )
        )

        self.assertEqual(result["url"], "https://example.com/article")

    def test_content_url_is_used_for_existing_google_news_rows(self):
        result = _serialize_news(
            _news_row(content="https://news.google.com/rss/articles/example")
        )

        self.assertEqual(
            result["url"],
            "https://news.google.com/rss/articles/example",
        )

    def test_plain_content_is_not_exposed_as_url(self):
        result = _serialize_news(_news_row(content="Article body"))

        self.assertIsNone(result["url"])


class NewsDateFilterTests(unittest.TestCase):
    def setUp(self):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=engine, tables=[News.__table__])
        self.db = sessionmaker(bind=engine)()
        self.db.add_all(
            [
                News(
                    external_id="news-2022",
                    category="TEST",
                    title="2022 news",
                    country="USA",
                    published_at=date(2022, 12, 31),
                ),
                News(
                    external_id="news-2023",
                    category="TEST",
                    title="2023 news",
                    country="USA",
                    published_at=date(2023, 6, 1),
                ),
                News(
                    external_id="news-2024",
                    category="TEST",
                    title="2024 news",
                    country="USA",
                    published_at=date(2024, 6, 1),
                ),
                News(
                    external_id="news-2025",
                    category="TEST",
                    title="2025 news",
                    country="USA",
                    published_at=date(2025, 1, 1),
                ),
            ]
        )
        self.db.commit()

    def tearDown(self):
        self.db.close()

    def test_news_are_filtered_by_inclusive_date_range(self):
        response = list_news(
            country="USA",
            limit=10,
            start_date=date(2023, 1, 1),
            end_date=date(2024, 12, 31),
            db=self.db,
        )

        self.assertEqual(
            [item["title"] for item in response],
            ["2024 news", "2023 news"],
        )


if __name__ == "__main__":
    unittest.main()
