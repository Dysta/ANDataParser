from __future__ import annotations

import argparse
import concurrent
import os
from math import inf

from loguru import logger

from .models import Scrutin
from .parsers import AmendementParser, ScrutinAnalyseParser, ScrutinParser


def process_amendement(scrutin: Scrutin):
    # ? Vérifie si l'amendement existe déjà, sinon le parse et le sauvegarde.
    if scrutin.text_url and "dossier" not in scrutin.text_url:
        parser = AmendementParser(scrutin.text_url)
        save_path = parser.save_data_target

        if os.path.exists(save_path):
            logger.info(f"Amendement déjà parsé : {save_path}")
            return

        try:
            parser.fetch_amendement_data()
            parser.save_json()
        except Exception as e:
            logger.error(f"Failed to fetch amendement {scrutin.text_url}: {e}")

        logger.success(f"Amendement traité : {save_path}")


def process_scrutin(scrutin: Scrutin):
    # ? Vérifie si le scrutin existe déjà, sinon le parse et le sauvegarde.
    if scrutin.url:
        parser = ScrutinAnalyseParser(scrutin.url)
        save_path = parser.save_data_target

        if os.path.exists(save_path):
            logger.info(f"scrutin déjà parsé : {save_path}")
            return

        try:
            parser.fetch_scrutin_analyse_data()
            parser.save_json()
        except Exception as e:
            logger.error(f"Failed to fetch scrutin {scrutin.url}: {e}")

        logger.success(f"Scrutin traité : {save_path}")


def main():
    parser = argparse.ArgumentParser("ANDataParser")
    parser.add_argument("--legislature", type=int, required=True, help="legislature number")
    parser.add_argument("--max_page", type=int, required=False, default=inf, help="max page to parse")
    args = parser.parse_args()

    dyn = ScrutinParser(legislature=args.legislature, max_page=args.max_page)
    dyn.parse_scrutins()
    dyn.save_json()
    logger.success(f"done, parsed {len(dyn.scrutins)} scrutins")

    with concurrent.futures.ProcessPoolExecutor() as executor:
        executor.map(process_scrutin, dyn.scrutins)

    with concurrent.futures.ProcessPoolExecutor() as executor:
        executor.map(process_amendement, dyn.scrutins)


main()
