from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from urllib.parse import urlparse, parse_qs

import os
import io
import time
import requests
import sqlite3
import pandas as pd


# Get no value from the url
def extract_no(url):
    # Parse
    parsed_url = urlparse(url)

    # Parse query parameters
    query_params = parse_qs(parsed_url.query)

    # Extract no value, or default to None
    no_value = query_params.get('no', [None])[0]

    return no_value


def main():
    # Set directory root path for saving files
    location = '../../data/'

    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))

    with sqlite3.connect('../db/webtoons.db') as conn:
        df = pd.read_sql_query('SELECT * FROM webtoons', conn)
        title_urls = df['url'].unique()

    # For each webtoon in the database make a driver request
    for title_url in title_urls:
        # Define headers
        headers = {
            'Accept': 'application/json, text/plain, image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': title_url,
            'Cookie': 'NNB=AR3Y7FOAVFNGG',
            'Content-Type': 'application/json; image/jpeg; charset=utf-8; */*'
        }
        try:
            driver.get(title_url)

            webtoon_title = driver.title.split(' : ')[0]
            print(f'Collecting episode urls for {webtoon_title}...')

            episode_urls = []
            page_numbers = []
            current_page = 1

            while True:
                # Get all episode urls on current page
                url_elements = driver.find_elements(By.CSS_SELECTOR, 'a.EpisodeListList__link--DdClU')

                episode_urls.extend([element.get_attribute('href') for element in url_elements])

                # Collect available page numbers
                pagination_buttons = driver.find_elements(By.CSS_SELECTOR, 'button.Paginate__page--iRmGj')
                page_numbers = [int(button.text) for button in pagination_buttons]

                # Check for the last page
                next_page = current_page + 1

                if next_page in page_numbers:
                    # Find next page button
                    next_button = driver.find_element(By.XPATH, f"//button[text()='{next_page}']")

                    # Exit if no more buttons
                    if not next_button:
                        break
                    
                    # Click the next page button
                    next_button.click()

                    # Update page
                    current_page = next_page

                    time.sleep(5)

            # Make request for each episode
            for episode_url in episode_urls:
                try:
                    driver.get(episode_url)

                    # Get episode number
                    episode_no = extract_no(episode_url)

                    # Directory to save episode
                    episode_dir = os.path.join(location, webtoon_title, episode_no)

                    # Create the directories if not exists
                    os.makedirs(episode_dir, exist_ok=True)

                    # Find all image elements with comic content
                    img_elements = driver.find_elements(By.CSS_SELECTOR, "img[alt='comic content']")
                    img_urls = [img.get_attribute('src') for img in img_elements]

                    # initialize filenames and pad with leading zeros
                    filename = '0'
                    filename = filename.zfill(4)

                    for img_url in img_urls:
                        download = requests.get(img_url, headers=headers)

                        # Save image to file
                        r = download.content
                        with open(f'{episode_dir}{filename}.jpg', 'wb+') as newfile:
                            newfile.write(r)
                        count = int(filename)
                        count += 1
                        filename = str(count).zfill(4)

            time.sleep(5)


        except Exception as e:
            print(f'Exception: {type(e).__name__} {e}')
            

if __name__ == '__main__':
    main()
