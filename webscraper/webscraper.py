from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
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


def kcomic_scrape():
    # Set directory root path for saving files
    location = '../data/'

    # Set the language
    language = 'korean'

    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920x1080')

    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)

    with sqlite3.connect('../db/webtoons.db') as conn:
        df = pd.read_sql_query('SELECT * FROM comics', conn)
        filtered_df = df[df['language'] == language]
        if filtered_df.empty:
            print(f"No {language} comics are in the database.")
            return
        title_urls = filtered_df['url'].unique()

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

            webtoon_title = driver.title.split(' :: ')[0]
            print(f'Collecting episode urls for {webtoon_title}...')

            # Clean the title for directory path compatibility
            webtoon_title = webtoon_title.lower()
            webtoon_title = webtoon_title.replace(" ", "_")

            episode_urls = []
            page_numbers = []
            current_page = 1

            while True:
                # Get all episode urls on current page
                episode_list = driver.find_element(By.CSS_SELECTOR, 'ul.section_episode_list')

                list_items = episode_list.find_elements(By.CSS_SELECTOR, 'li:not(.lock)')

                # Create a new list for URLs in this loop
                current_urls = [element.find_element(By.CSS_SELECTOR, 'a').get_attribute('href') for element in list_items]
                
                # Extend episode_urls with newly fetched URLs
                episode_urls.extend(current_urls)

                # Determine if there is a next button for pagination, and if not use numbered pagination
                btn_next = driver.find_element(By.CLASS_NAME, 'btn_next')

                if btn_next:
                    # Break if the next button is disabled
                    disabled = 'disabled'
                    if disabled in btn_next.get_attribute('class'):
                        break
                    else:
                        btn_next.click()

                else:
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

            # Determine how many episodes are already downloaded and use that number to reduce the list to download
            comic_dir = os.path.join(location, language, webtoon_title)

            if os.path.exists(comic_dir):  # Check that the directory exists
                saved_episodes = os.listdir(comic_dir)
                if saved_episodes:
                    num_episodes = len(saved_episodes)
                else:
                    num_episodes = 0
            else:
                num_episodes = 0  # If the directory does not exist, there are 0 saved episodes

            download_episode_urls = episode_urls[num_episodes:]

            # Make request for each episode
            for episode_url in download_episode_urls:
                try:
                    driver.get(episode_url)
                    time.sleep(10)

                    # Get episode number
                    episode_no = extract_no(episode_url)

                    # Directory to save episode
                    episode_dir = os.path.join(location, language, webtoon_title, episode_no.zfill(3))

                    # Create the directories if not exists
                    os.makedirs(episode_dir, exist_ok=True)

                    comic_layer = driver.find_element(By.CLASS_NAME, 'toon_view_lst')

                    # Find all image elements with comic content
                    img_elements = comic_layer.find_elements(By.CSS_SELECTOR, 'img')
                    img_urls = [img.get_attribute('data-src') or img.get_attribute('src') for img in img_elements]

                    # initialize filenames and pad with leading zeros
                    filename = '0'
                    filename = filename.zfill(3)

                    for img_url in img_urls:
                        download = requests.get(img_url, headers=headers)

                        # Save image to file
                        r = download.content
                        with open(f'{episode_dir}/{filename}.jpg', 'wb+') as newfile:
                            newfile.write(r)
                        count = int(filename)
                        count += 1
                        filename = str(count).zfill(3)
                    
                    # Prevent rapid requests
                    time.sleep(5)


                except Exception as e:
                    print(f'Exception: {type(e).__name__} {e}')

            # Prevent rapid requests
            time.sleep(5)


        except Exception as e:
            print(f'Exception: {type(e).__name__} {e}')
    driver.quit()
  

if __name__ == '__main__':
    kcomic_scrape()
