from __future__ import annotations

import argparse
import concurrent
import os
from math import inf

from loguru import logger

from .models import Scrutin
from .parsers import AmendementParser, ScrutinParser


def process_amendement(scrutin: Scrutin):
    # ? Vérifie si l'amendement existe déjà, sinon le parse et le sauvegarde.
    if scrutin.text_url and "dossier" not in scrutin.text_url:
        parser = AmendementParser(scrutin.text_url)
        save_path = parser.save_data_target  # L'endroit où il est sauvegardé

        if os.path.exists(save_path):
            logger.info(f"Amendement déjà parsé : {save_path}")
            return

        parser.fetch_amendement_data()
        parser.save_json()

        logger.debug(f"Amendement traité : {parser}")


def main():
    parser = argparse.ArgumentParser("ANDataParser")
    parser.add_argument("--legislature", type=int, required=True, help="legislature number")
    parser.add_argument("--max_page", type=int, required=False, default=inf, help="max page to parse")
    args = parser.parse_args()

    dyn17 = ScrutinParser(legislature=args.legislature, max_page=args.max_page)
    dyn17.parse_scrutins()
    dyn17.save_json()
    logger.success(f"done, parsed {len(dyn17.scrutins)} scrutins")

    with concurrent.futures.ProcessPoolExecutor() as executor:
        executor.map(process_amendement, dyn17.scrutins)


main()
