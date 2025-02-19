import json

from loguru import logger

from .parsers import ScrutinParser


def main():
    dyn17 = ScrutinParser(legislature=17)
    dyn17.parse_scrutins()
    dyn17.save_json()
    logger.success(f"done, parsed {len(dyn17.scrutins)} scrutins")

    dyn16 = ScrutinParser(legislature=16)
    dyn16.parse_scrutins()
    dyn16.save_json()
    logger.success(f"done, parsed {len(dyn16.scrutins)} scrutins")


main()
