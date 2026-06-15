import unittest
from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.v1.endpoints.indicators import (
    indicator_scores,
    indicator_summary,
    score_trend,
)
from app.db.session import Base
from app.models.esg_stat import ESGStat


class IndicatorEndpointTests(unittest.TestCase):
    def setUp(self):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=engine, tables=[ESGStat.__table__])
        self.db = sessionmaker(bind=engine)()

        rows = []
        indicator_values = {
            "energy_consumption_risk": ("E", 95.0, 100.0, 105.0),
            "unemployment_risk": ("S", 4.5, 4.0, 3.5),
            "life_expectancy_risk": ("S", 79.0, 80.0, 81.0),
            "freedom_governance_risk": ("G", 76.0, 78.0, 80.0),
        }
        for risk_type, (category, value_2022, value_2023, value_2024) in indicator_values.items():
            for year, value in (
                (2022, value_2022),
                (2023, value_2023),
                (2024, value_2024),
            ):
                rows.append(
                    ESGStat(
                        category=category,
                        risk_type=risk_type,
                        country="Korea, Rep.",
                        country_code="KOR",
                        indicator=risk_type,
                        indicator_code=risk_type,
                        year=year,
                        value=value,
                    )
                )

        self.db.add_all(rows)
        self.db.commit()

    def tearDown(self):
        self.db.close()

    def test_summary_returns_all_dashboard_indicators(self):
        response = indicator_summary(country="KOR", limit=4, db=self.db)

        self.assertEqual(response["total"], 4)
        self.assertEqual(
            {item["risk_type"] for item in response["items"]},
            {
                "energy_consumption_risk",
                "unemployment_risk",
                "life_expectancy_risk",
                "freedom_governance_risk",
            },
        )

    def test_scores_return_all_esg_categories(self):
        response = indicator_scores(country="KOR", db=self.db)

        self.assertEqual(set(response["scores"]), {"E", "S", "G"})
        self.assertIsNotNone(response["overall"])
        self.assertIsNotNone(response["previous_overall"])
        self.assertIsNotNone(response["overall_change"])

    def test_trend_requires_and_returns_complete_esg_years(self):
        response = score_trend(country="KOR", limit=6, db=self.db)

        self.assertEqual(response["total"], 3)
        self.assertEqual(
            [item["year"] for item in response["items"]],
            [2022, 2023, 2024],
        )
        self.assertTrue(
            all(set(item["scores"]) == {"E", "S", "G"} for item in response["items"])
        )

    def test_summary_uses_only_selected_year_range(self):
        response = indicator_summary(
            country="KOR",
            limit=4,
            start_date=date(2023, 1, 1),
            end_date=date(2023, 12, 31),
            db=self.db,
        )

        self.assertTrue(all(item["year"] == 2023 for item in response["items"]))
        self.assertTrue(
            all(item["previous_year"] is None for item in response["items"])
        )

    def test_scores_use_latest_rows_inside_selected_year_range(self):
        response = indicator_scores(
            country="KOR",
            start_date=date(2023, 1, 1),
            end_date=date(2024, 12, 31),
            db=self.db,
        )

        self.assertEqual(set(response["scores"]), {"E", "S", "G"})
        self.assertIsNotNone(response["previous_overall"])

    def test_trend_returns_only_years_inside_selected_range(self):
        response = score_trend(
            country="KOR",
            limit=6,
            start_date=date(2023, 1, 1),
            end_date=date(2024, 12, 31),
            db=self.db,
        )

        self.assertEqual(
            [item["year"] for item in response["items"]],
            [2023, 2024],
        )


if __name__ == "__main__":
    unittest.main()
