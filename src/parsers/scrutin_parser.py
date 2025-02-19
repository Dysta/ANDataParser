from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import dateparser
import requests
from bs4 import BeautifulSoup
from loguru import logger

from src.models import Scrutin, ScrutinAnalyse

if TYPE_CHECKING:
    from typing import List, Tuple

DATE_REGX = re.compile(
    r"(lundi|mardi|mercredi|jeudi|vendredi|samedi|dimanche) (\d{1,2})(er)? [a-zéû]+ \d{4}",  # ? should match Lundi 17 mars 2022 in scrutin title
    re.IGNORECASE,
)

BASE_URL: str = "https://www.assemblee-nationale.fr/dyn"


@dataclass(eq=False, init=False)
class ScrutinParser:
    scrutins: List[Scrutin] = field(default_factory=list)
    total_page: int = 0
    save_data_target: str = "data/dyn/%d/scrutins.json"

    legislature: int

    def __init__(self, legislature: int):
        self.legislature = legislature
        self.save_data_target = self.save_data_target % self.legislature

    def _fetch_page(self, an_url: str) -> BeautifulSoup:
        logger.debug(f"Fetch url {an_url}")
        resp = requests.get(an_url)
        if resp.status_code != 200:
            raise Exception(f"Failed to fetch page {an_url}")

        return BeautifulSoup(resp.text, "html.parser")

    def _parse_date(self, date: str) -> str:
        """Transform a string "Lundi 16 janvier 2025 into a datetime object"""
        date_match = re.search(
            DATE_REGX,
            date,
        )
        if not date_match:
            # ? some scrutins doesn't have date in the title
            logger.warning(f"No date found for scrutin {date}")
            return ""

        group = date_match.group(0).capitalize()
        return dateparser.parse(group, languages=["fr"]).strftime("%Y-%m-%d")

    def _parse_vote(self, div: BeautifulSoup, title: str) -> Tuple[int, int, int]:
        # ? we try to find the normal div where there is 3 results (for, against, abstention)
        vote_div = div.find("ul", class_="votes-list")
        if vote_div:
            votes = vote_div.find_all("li")
            # ? votes are always ordered: for, against, abstention
            vote_for = int(votes[0].find("b").get_text(strip=True))
            vote_against = int(votes[1].find("b").get_text(strip=True))
            vote_abstention = int(votes[2].find("b").get_text(strip=True))

            return vote_for, vote_against, vote_abstention

        # ? for motion de censure, there is only for vote and the div have a different class
        vote_div = div.find("div", class_="flex1 _gutter-xs _vertical")
        if vote_div:
            vote = vote_div.find_all("span", class_="_colored-primary")
            vote_for = int(vote[1].find("b").get_text(strip=True))
            vote_against = -1
            vote_abstention = -1

            return vote_for, vote_against, vote_abstention

        raise Exception(f"Vote not found for scrutin {title}")

    def _parse_url(self, div: BeautifulSoup) -> Tuple[str, str]:
        ul = div.find("ul", class_="button-list _vertical _align-end")
        li = ul.find_all("li")
        # ? first li should be the scrutin url
        # ? second li should be the law text url
        url = li[0].find("a")["href"]
        text_url = ""
        if len(li) == 2:
            text_url = (
                li[1].find("a")["href"].replace("https://www.assemblee-nationale.fr", "")
            )  # ? law text have url in it so we remove it

        return url, text_url

    def _parse_total_pages(self, an_url: str) -> int:
        soup = self._fetch_page(an_url)
        pagination_div = soup.find("div", class_="an-pagination")
        # ? return a list of div that contain the number of page like
        # ? < 1 2 ... X >
        pagination_items = pagination_div.find_all("div", class_="an-pagination--item")
        # ? we retrieve the index -2 to ignore the > and retrieve the X
        self.total_page = int(pagination_items[-2].get_text(strip=True))
        logger.debug(f"Total pages: {self.total_page}")

    def save_json(self):
        data = {
            "total": len(self.scrutins),
            "scrutins": [scrutin.__dict__ for scrutin in self.scrutins],
        }

        os.makedirs(os.path.dirname(self.save_data_target), exist_ok=True)

        with open(self.save_data_target, "w") as f:
            f.write(json.dumps(data))

    def parse_scrutins(self):
        scrutins: List[Scrutin] = []
        an_url: str = f"{BASE_URL}/{self.legislature}/scrutins?order=date,desc&limit=100"

        if self.total_page == 0:
            self._parse_total_pages(an_url)

        for page in range(1, self.total_page + 1):
            soup = self._fetch_page(an_url + f"&page={page}")
            scrutin_divs = soup.find_all("div", class_="an-bloc _style-scrutin")

            logger.info(f"Found {len(scrutin_divs)} scrutins on page {page}")

            for div in scrutin_divs:
                try:
                    # * Extract relevant information from each div
                    title = div.find("a", class_="link h6").get_text(strip=True)
                    url, text_url = self._parse_url(div)
                    id = int(url.split("/")[-1])  # ? id is the last part of the url

                    date = div.find("span", class_="h6 _colored-primary").get_text(strip=True)
                    date = self._parse_date(date)

                    adopted = True if div.find("span", class_="_colored-green _bold") else False

                    vote_for, vote_against, vote_abstention = self._parse_vote(div, title)

                    scrutin = Scrutin(
                        id=id,
                        name=title,
                        url=url,
                        text_url=text_url,
                        date=date,
                        adopted=adopted,
                        vote_for=vote_for,
                        vote_against=vote_against,
                        vote_abstention=vote_abstention,
                    )
                    scrutins.append(scrutin)
                except Exception as e:
                    logger.error(f"Error while parsing scrutin {url}: {e}")

        self.scrutins = scrutins
