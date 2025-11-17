import logging
from src.main import instasea

@instasea.command(help="Collecting pending messages to database.")
def collect():
    logging.info("Soon!")
    