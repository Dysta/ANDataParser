import unittest
from unittest.mock import patch

from bs4 import BeautifulSoup

from src.models import ScrutinAnalyse
from src.parsers import ScrutinAnalyseParser


class TestScrutinAnalyse(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        with open("tests/data/scrutin_analyse_data.html", "r", encoding="utf-8") as f:
            cls.sample_html = f.read()

    def setUp(self) -> None:
        # ? link is required since id is extracted from the url
        self.parser = ScrutinAnalyseParser(am_url="https://www.assemblee-nationale.fr/dyn/17/scrutins/3186")

        patch_fetch_page = patch.object(ScrutinAnalyseParser, "_fetch_page", side_effect=self.mock_fetch_page)
        patch_fetch_vizu = patch.object(
            ScrutinAnalyseParser, "_extract_visualiser", side_effect=self.mock_fetch_vizualizer
        )

        self.mocked_fetch_page = patch_fetch_page.start()
        self.mocked_fetch_vizu = patch_fetch_vizu.start()

        self.addCleanup(patch_fetch_page.stop)
        self.addCleanup(patch_fetch_vizu.stop)

    def mock_fetch_page(self, url: str):
        return BeautifulSoup(self.sample_html, "html.parser")

    def mock_fetch_vizualizer(self, visualiser_url: str) -> str:
        # ? extract the url from the sample html to simulate the process
        # ? real vizualizer requires selenium so we just return the url here
        page = BeautifulSoup(self.sample_html, "html.parser")
        visualizer_url = page.find("div", attrs={"data-targetembedid": "embedHemicycle"})
        url = visualizer_url.get("data-content")

        return url

    def test_fetch_scrutin_analyse_data(self):
        self.parser.fetch_scrutin_analyse_data()
        self.assertIsInstance(self.parser.scrutin_analyse, ScrutinAnalyse)
        self.assertEqual(self.mocked_fetch_page.call_count, 1)

        self.assertEqual(self.parser.scrutin_analyse.id, 3186)
        self.assertEqual(self.parser.scrutin_analyse.date, "2025-10-28")
        self.assertEqual(
            self.parser.scrutin_analyse.title,
            "Scrutin public n°3186 sur l'amendement n° 2493 de M. Prud'homme après l'article 12 (examen prioritaire) du projet de loi de finances pour 2026 (première lecture).",
        )

        self.assertIsNotNone(self.parser.scrutin_analyse.visualizer)
        self.assertIn("hemicycle", self.parser.scrutin_analyse.visualizer)

        self.assertIsInstance(self.parser.scrutin_analyse.vote_for, list)
        self.assertEqual(len(self.parser.scrutin_analyse.vote_for), 42)

        self.assertIsInstance(self.parser.scrutin_analyse.vote_against, list)
        self.assertEqual(len(self.parser.scrutin_analyse.vote_against), 178)

        self.assertIsInstance(self.parser.scrutin_analyse.vote_abstention, list)
        self.assertEqual(len(self.parser.scrutin_analyse.vote_abstention), 6)

        self.assertIsInstance(self.parser.scrutin_analyse.vote_absent, list)
        self.assertEqual(len(self.parser.scrutin_analyse.vote_absent), 15)

        self.assertFalse(self.parser.scrutin_analyse.adopted)
