import unittest
from unittest.mock import patch

from bs4 import BeautifulSoup

from src.models import Scrutin
from src.parsers import ScrutinParser


class TestScrutinParser(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        with open("tests/data/scrutins_data.html", "r", encoding="utf-8") as f:
            cls.sample_html = f.read()

    def setUp(self) -> None:
        self.parser = ScrutinParser(legislature=17, max_page=1)

        patch_fetch_page = patch.object(ScrutinParser, "_fetch_page", side_effect=self.mock_fetch_page)

        self.mocked_fetch_page = patch_fetch_page.start()

        self.addCleanup(patch_fetch_page.stop)

    def mock_fetch_page(self, an_url: str):
        return BeautifulSoup(self.sample_html, "html.parser")

    def test_parse_scrutins(self):
        self.parser.parse_scrutins()
        self.assertEqual(self.mocked_fetch_page.call_count, 2)

        self.assertIsInstance(self.parser.scrutins, list)
        self.assertEqual(len(self.parser.scrutins), 10)

        expected_ids = [3159, 3160, 3124, 3125, 3166, 3165, 3167, 3137, 3168, 3150]

        for scrutin in self.parser.scrutins:
            self.assertIsInstance(scrutin, Scrutin)
            self.assertIsNotNone(scrutin.id)
            self.assertIsInstance(scrutin.id, int)
            self.assertIn(scrutin.id, expected_ids)

            self.assertIsNotNone(scrutin.name)
            self.assertIsInstance(scrutin.name, str)

            self.assertIsNotNone(scrutin.url)
            self.assertIsInstance(scrutin.url, str)

            self.assertIsNotNone(scrutin.text_url)
            self.assertIsInstance(scrutin.text_url, str)

            self.assertIsNotNone(scrutin.date)
            self.assertIsInstance(scrutin.date, str)

            self.assertIsInstance(scrutin.adopted, bool)

            self.assertIsNotNone(scrutin.vote_for)
            self.assertIsInstance(scrutin.vote_for, int)

            self.assertIsNotNone(scrutin.vote_against)
            self.assertIsInstance(scrutin.vote_against, int)

            self.assertIsNotNone(scrutin.vote_abstention)
            self.assertIsInstance(scrutin.vote_abstention, int)
