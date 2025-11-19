from webscraper.webscraper import kcomic_scrape
from webscraper.webscraper_en import ecomic_scrape

import schedule
import time
import threading


def run_scheduler():
    schedule.every().wednesday.at("00:00").do(kcomic_scrape)
    schedule.every().sunday.at("00:00").do(ecomic_scrape)

    while True:
        schedule.run_pending()
        time.sleep(1)

def start_scheduler():
    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.start()
