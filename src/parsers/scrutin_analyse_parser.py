from __future__ import annotations

import json
import os
from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup
from cattr import unstructure
from loguru import logger
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

import src.helpers as helpers
from src.models import Depute, ScrutinAnalyse

BASE_URL: str = "https://www.assemblee-nationale.fr"


@dataclass(eq=False, init=False)
class ScrutinAnalyseParser:
    scrutin_analyse: ScrutinAnalyse
    scrutin_url: str
    save_data_target: str = "data%s.json"

    def __init__(self, am_url: str):
        self.scrutin_url = am_url
        self.save_data_target = self.save_data_target % am_url

    def _fetch_page(self, url: str) -> BeautifulSoup:
        url = BASE_URL + url
        logger.debug(f"Fetch url {url}")
        resp = requests.get(url)
        if resp.status_code != 200:
            raise Exception(f"Failed to fetch page {url}")

        return BeautifulSoup(resp.text, "html.parser")

    def _extract_visualiser(self, visualiser_url: str) -> str:
        vizu_url = BASE_URL + visualiser_url

        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--incognito")

        driver = webdriver.Chrome(options=options)
        driver.set_window_size(800, 800)

        driver.get(vizu_url)
        driver.implicitly_wait(3)

        driver.execute_script(f"window.scrollTo(0, 335);")

        vizu = driver.find_element(By.CSS_SELECTOR, ".hemicycle-carte-svg")
        b64 = vizu.screenshot_as_base64

        driver.quit()

        return b64

    def fetch_scrutin_analyse_data(self) -> None:
        page = self._fetch_page(self.scrutin_url)
        repartition = page.find("div", class_="ha-grid-item _size-3")

        groups = repartition.find_all("ul", class_="simple-tree-list _large-border")

        infos_div = page.find("div", class_="relative-flex _vertical")
        date = infos_div.find("h2").get_text(strip=True)
        date = helpers.parse_date(date)

        title = infos_div.find("p").get_text(strip=True)
        adopted = True if page.find("span", class_="_colored-green _bold") else False

        vote_for = vote_against = vote_abstention = vote_absent = []

        visualizer_url = page.find("div", attrs={"data-targetembedid": "embedHemicycle"})
        b64_vizualiser = ""
        if visualizer_url:  # ? some scrutins don't have a visualizer
            url = visualizer_url.get("data-content")
            b64_vizualiser = self._extract_visualiser(url)

        for group in groups:
            group_name: str = group.get("id").replace("groupe", "")

            group_info_li = group.find_all("li", class_="relative-flex _vertical")
            for info in group_info_li:
                vote_infos = info.find_all("span")
                vote_type = vote_infos[0].get_text(strip=True)
                vote_result = vote_infos[1].get_text(strip=True)

                voters_ul = info.find("ul")
                for voter in voters_ul.find_all("li"):
                    voter_name = voter.get_text(strip=True)
                    first_name, last_name = helpers.parse_name(voter_name)

                    dep = Depute(first_name=first_name, last_name=last_name, party=group_name)

                    if vote_type == "Pour":
                        vote_for.append(dep)
                    elif vote_type == "Contre":
                        vote_against.append(dep)
                    elif vote_type == "Abstention":
                        vote_abstention.append(dep)
                    elif vote_type == "Non votant":
                        vote_absent.append(dep)
                    else:
                        raise Exception(f"Unknown vote type {vote_type}")

        self.scrutin_analyse = ScrutinAnalyse(
            id=int(self.scrutin_url.split("/")[-1]),
            date=date,
            title=title,
            adopted=adopted,
            visualizer=b64_vizualiser,
            vote_for=vote_for,
            vote_against=vote_against,
            vote_abstention=vote_abstention,
            vote_absent=vote_absent,
        )

    def save_json(self) -> None:
        data = {
            "id": self.scrutin_analyse.id,
            "date": self.scrutin_analyse.date,
            "title": self.scrutin_analyse.title,
            "adopted": self.scrutin_analyse.adopted,
            "visualizer": self.scrutin_analyse.visualizer,
            "vote_for": [unstructure(d) for d in self.scrutin_analyse.vote_for],
            "vote_against": [unstructure(d) for d in self.scrutin_analyse.vote_against],
            "vote_abstention": [unstructure(d) for d in self.scrutin_analyse.vote_abstention],
            "vote_absent": [unstructure(d) for d in self.scrutin_analyse.vote_absent],
        }

        os.makedirs(os.path.dirname(self.save_data_target), exist_ok=True)

        with open(self.save_data_target, "w") as f:
            f.write(json.dumps(data))
