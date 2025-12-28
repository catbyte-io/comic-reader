from celery import Celery
from celery.schedules import crontab
from webscraper.webscraper import kcomic_scrape
from webscraper.webscraper_en import ecomic_scrape

def register_tasks(celery: Celery):
    @celery.task
    def kcomic_task():
        kcomic_scrape()

    @celery.task
    def ecomic_task():
        ecomic_scrape()

    # Schedule tasks
    celery.conf.beat_schedule = {
        'kcomic-scrape-every-wednesday': {
            'task': 'tasks.celery_tasks.kcomic_task',
            'schedule': crontab(day_of_week='wed', hour=0, minute=0),
        },
        'ecomic-scrape-every-sunday': {
            'task': 'tasks.celery_tasks.ecomic_task',
            'schedule': crontab(day_of_week='sun', hour=0, minute=0),
        },
    }
    