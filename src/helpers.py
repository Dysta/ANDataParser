from __future__ import annotations

import re
from typing import Tuple

import dateparser
from loguru import logger

DATE_REGX = re.compile(
    r"(lundi|mardi|mercredi|jeudi|vendredi|samedi|dimanche) (\d{1,2})(er)? [a-zéû]+ \d{4}",  # ? should match Lundi 17 mars 2022 in scrutin title
    re.IGNORECASE,
)


def parse_date(date: str) -> str:
    """Transform a string "Lundi 16 janvier 2025" into a datetime object"""
    date_match = re.search(
        DATE_REGX,
        date,
    )
    if not date_match:
        # ? some scrutins doesn't have date in the title
        logger.warning(f"No date found for raw date {date}")
        return ""

    group = date_match.group(0).capitalize()
    return dateparser.parse(group, languages=["fr"]).strftime("%Y-%m-%d")


def parse_name(name: str) -> Tuple[str, str]:
    splited_name = name.split(" ")  # ? we split to remove the gender prefix
    # ? we remove the gender prefix
    splited_name = splited_name[1:]
    # ? some depute have a composed name like Marc de Fleurian
    # ? so we take the first entry as first name
    first_name = splited_name[0]
    # ? and the rest as last name
    last_name = " ".join(splited_name[1:])

    return first_name, last_name
