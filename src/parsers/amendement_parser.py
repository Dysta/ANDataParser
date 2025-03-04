from __future__ import annotations

import json
import os
from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup
from cattr import unstructure
from loguru import logger

import src.helpers as helpers
from src.models import Amendement, Depute

BASE_URL: str = "https://www.assemblee-nationale.fr"


@dataclass(eq=False, init=False)
class AmendementParser:
    amendement: Amendement
    am_url: str
    save_data_target: str = "data/%s.json"

    def __init__(self, am_url: str):
        self.am_url = am_url
        self.save_data_target = self.save_data_target % am_url

    def _fetch_page(self, am_url: str) -> BeautifulSoup:
        am_url = BASE_URL + am_url
        logger.debug(f"Fetch url {am_url}")
        resp = requests.get(am_url)
        if resp.status_code != 200:
            raise Exception(f"Failed to fetch page {am_url}")

        return BeautifulSoup(resp.text, "html.parser")

    def fetch_amendement_data(self) -> None:
        page = self._fetch_page(self.am_url)

        # ? return 3 div with the same class name.
        # ? The first one is the votants, the second one is the article, the third one is the summary
        summary_div = page.find_all("div", class_="amendement-section-body")
        summary = "\n".join([p.get_text(strip=True) for p in summary_div[-1].find_all("p")])

        # ? check if its the government that submitted the amendement
        submitted_by_government = "Le Gouvernement" in summary_div[0].get_text(strip=True)

        if submitted_by_government:
            proposed_by = "Le Gouvernement"
        else:
            # ? Récupérer les députés proposant l'amendement
            proposed_by_li = page.find("ul", class_="acteur-list-embed--names").find_all("li")
            proposed_by = []
            for li in proposed_by_li:
                name = li.find("span").get_text(strip=True)  # ? le nom est dans le span
                splited_name = name.split(" ")  # ? we split to remove the gender prefix
                # ? we remove the gender prefix
                splited_name = splited_name[1:]
                # ? some depute have a composed name like Marc de Fleurian
                # ? so we take the first entry as first name
                first_name = splited_name[0]
                # ? and the rest as last name
                last_name = " ".join(splited_name[1:])

                # ? each depute has a data-nom div set to their full name
                # ? the party is in the data-gp attribute
                party = page.find("div", {"data-nom": first_name + " " + last_name}).get("data-gp")

                dep = Depute(first_name=first_name, last_name=last_name, party=party)

                proposed_by.append(dep)

        status = page.find("div", class_="amendement-fate").find("span").get_text(strip=True)

        date = page.find("div", class_="mirror-card-subtitle").find("b").get_text(strip=True)
        date = helpers.parse_date(date)

        name = page.find("div", class_="amendement-detail").find_all("span")[1].get_text(strip=True)

        # ? id is the last element of the url
        id = int(self.am_url.split("/")[-1])

        amd = Amendement(
            id=id,
            name=name,
            url=self.am_url,
            date=date,
            status=status,
            proposed_by=proposed_by,
            summary=summary,
        )

        self.amendement = amd

    def save_json(self) -> None:
        os.makedirs(os.path.dirname(self.save_data_target), exist_ok=True)

        with open(self.save_data_target, "w") as f:
            f.write(json.dumps(unstructure(self.amendement)))
