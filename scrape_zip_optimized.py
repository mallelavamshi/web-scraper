#!/usr/bin/env python3

"""
Multi-Threaded Google Maps Scraper with Anti-Detection Features
Optimized for Linux/Docker deployment
Author: Auto-generated (Linux-compatible version)
Date: 2025
"""

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import time
import pandas as pd
import re
import os
import random
import subprocess
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [Thread-%(thread)d] - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Thread-safe locks
print_lock = threading.Lock()
file_lock = threading.Lock()

# User agents for rotation
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
]

def safe_print(message):
    """Thread-safe printing"""
    with print_lock:
        print(message)
        sys.stdout.flush()

def get_chrome_version():
    """Get Chrome version - Linux compatible"""
    try:
        result = subprocess.run(['google-chrome', '--version'], 
                              capture_output=True, text=True)
        version = result.stdout.split()[2]
        return int(version.split('.')[0])
    except:
        try:
            result = subprocess.run(['chromium', '--version'], 
                                  capture_output=True, text=True)
            version = result.stdout.split()[1]
            return int(version.split('.')[0])
        except:
            return None

def human_delay(min_sec=2, max_sec=5):
    """Simulate human-like delay"""
    time.sleep(random.uniform(min_sec, max_sec))

def init_driver(thread_id=0):
    """Initialize undetected Chrome driver with anti-detection features"""
    safe_print(f"[Thread-{thread_id}] Initializing browser...")

    options = uc.ChromeOptions()
    options.add_argument('--headless=new')
    options.add_argument(f'user-agent={random.choice(USER_AGENTS)}')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--start-maximized')
    options.add_argument('--disable-notifications')
    options.add_argument('--disable-popup-blocking')

    chrome_version = get_chrome_version()
    if chrome_version:
        logger.info(f"Chrome version detected: {chrome_version}")
        driver = uc.Chrome(options=options, version_main=chrome_version, use_subprocess=True)
    else:
        logger.info("Could not detect Chrome version, using default...")
        driver = uc.Chrome(options=options, use_subprocess=True)

    safe_print(f"[Thread-{thread_id}] ✓ Browser initialized!")
    return driver

def search_query(driver, query, thread_id=0):
    """Search Google Maps with human-like typing"""
    driver.get("https://www.google.com/maps")
    human_delay(3, 5)

    try:
        search_box = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, "searchboxinput"))
        )

        search_box.clear()
        human_delay(0.5, 1)

        # Type like a human - one character at a time
        for char in query:
            search_box.send_keys(char)
            time.sleep(random.uniform(0.05, 0.15))

        human_delay(0.5, 1.5)
        search_box.send_keys(Keys.ENTER)
        human_delay(5, 7)  # Wait for results to load

        safe_print(f"[Thread-{thread_id}] ✓ Searched: {query}")
        return True
    except Exception as e:
        logger.error(f"[Thread-{thread_id}] Search error: {e}")
        return False

def simulate_human_behavior(driver):
    """Simulate random mouse movements"""
    try:
        action = ActionChains(driver)
        x_offset = random.randint(50, 200)
        y_offset = random.randint(50, 200)
        action.move_by_offset(x_offset, y_offset).perform()
        time.sleep(random.uniform(0.3, 0.8))
    except:
        pass

def scroll_results(driver, max_scrolls=15, thread_id=0):
    """Scroll through results with human-like behavior"""
    safe_print(f"[Thread-{thread_id}] Scrolling results...")

    try:
        scrollable = driver.find_element(By.CSS_SELECTOR, 'div[role="feed"]')
        previous_height = 0
        scroll_count = 0

        for i in range(max_scrolls):
            # Add human behavior every 3 scrolls
            if i % 3 == 0:
                simulate_human_behavior(driver)

            driver.execute_script('arguments[0].scrollTop = arguments[0].scrollHeight', scrollable)

            # Human-like pause between scrolls
            pause_time = random.uniform(2, 4)
            time.sleep(pause_time)

            current_height = driver.execute_script('return arguments[0].scrollTop', scrollable)

            if current_height == previous_height:
                safe_print(f"[Thread-{thread_id}] Reached end at scroll {i + 1}")
                break

            previous_height = current_height
            scroll_count += 1

            if (i + 1) % 3 == 0:
                safe_print(f"[Thread-{thread_id}] Scrolled {i + 1} times...")

        safe_print(f"[Thread-{thread_id}] ✓ Completed {scroll_count} scrolls")
        human_delay(2, 3)
        return True

    except Exception as e:
        logger.error(f"[Thread-{thread_id}] Scroll error: {e}")
        return False

def extract_business_details(driver, card, index, thread_id=0):
    """Extract details from a single business card"""
    try:
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", card)
        human_delay(0.5, 1)
        card.click()
        human_delay(2, 3.5)

        # Extract name
        try:
            name = driver.find_element(By.CSS_SELECTOR, "h1.DUwDvf").text
        except:
            try:
                name = driver.find_element(By.CSS_SELECTOR, "h1.fontHeadlineLarge").text
            except:
                name = ""

        # Extract rating
        try:
            rating_element = driver.find_element(By.CSS_SELECTOR, "span.ceNzKf")
            rating = rating_element.get_attribute("aria-label").split()[0]
        except:
            try:
                rating = driver.find_element(By.CSS_SELECTOR, "div.F7nice span").text
            except:
                rating = ""

        # Extract location
        try:
            location = driver.find_element(By.CSS_SELECTOR, "button[data-item-id='address']").get_attribute("aria-label")
            location = location.replace("Address: ", "").replace("Address:", "").strip()
        except:
            try:
                location = driver.find_element(By.CSS_SELECTOR, "button[data-tooltip='Copy address']").get_attribute("aria-label")
            except:
                location = ""

        # Extract phone
        try:
            phone = driver.find_element(By.CSS_SELECTOR, "button[data-item-id^='phone:tel:']").get_attribute("aria-label")
            phone = phone.replace("Phone: ", "").replace("Phone:", "").strip()
        except:
            try:
                phone = driver.find_element(By.CSS_SELECTOR, "button[data-tooltip='Copy phone number']").get_attribute("aria-label")
            except:
                phone = ""

        # Extract website
        try:
            website = driver.find_element(By.CSS_SELECTOR, "a[data-item-id='authority']").get_attribute("href")
        except:
            try:
                website_element = driver.find_element(By.CSS_SELECTOR, "a[aria-label*='Website']")
                website = website_element.get_attribute("href")
            except:
                website = ""

        return {
            "Name": name,
            "Location": location,
            "Phone Number": phone,
            "Email Address": "",
            "Rating": rating,
            "Website": website
        }

    except Exception as e:
        logger.error(f"[Thread-{thread_id}] Error extracting business {index}: {str(e)[:50]}")
        return None

def parse_cards_with_details(driver, thread_id=0):
    """Extract all business cards from the feed"""
    safe_print(f"[Thread-{thread_id}] Extracting business data...")

    try:
        feed_container = driver.find_element(By.CSS_SELECTOR, 'div[role="feed"]')
        cards = feed_container.find_elements(By.CSS_SELECTOR, "div.Nv2PK")
        total_cards = len(cards)

        safe_print(f"[Thread-{thread_id}] ✓ Found {total_cards} listings")

        if total_cards == 0:
            safe_print(f"[Thread-{thread_id}] ⚠ No business cards found")
            return []

        data = []
        request_count = 0
        start_time = time.time()

        for idx, card in enumerate(cards):
            try:
                # Rate limiting: pause after every 5 requests
                if request_count >= 5:
                    elapsed = time.time() - start_time
                    if elapsed < 60:
                        wait_time = 60 - elapsed
                        safe_print(f"[Thread-{thread_id}] ⏸ Rate limiting: waiting {wait_time:.1f}s...")
                        time.sleep(wait_time)
                    request_count = 0
                    start_time = time.time()

                details = extract_business_details(driver, card, idx + 1, thread_id)

                if details and details.get("Name"):
                    data.append(details)
                    safe_print(f"[Thread-{thread_id}] ✓ [{idx + 1}/{total_cards}]: {details['Name'][:50]}")
                else:
                    safe_print(f"[Thread-{thread_id}] ⚠ Skipped [{idx + 1}/{total_cards}]: No data")

                request_count += 1
                human_delay(1.5, 3)

            except Exception as e:
                logger.error(f"[Thread-{thread_id}] Error processing card {idx + 1}: {str(e)[:50]}")
                continue

        safe_print(f"[Thread-{thread_id}] ✓ Successfully extracted {len(data)} out of {total_cards}")
        return data

    except Exception as e:
        logger.error(f"[Thread-{thread_id}] Error in parse_cards: {e}")
        return []

def save_data_to_excel(data, folder_name, query, thread_id=0):
    """Save extracted data to Excel file"""
    if not data:
        safe_print(f"[Thread-{thread_id}] ⚠ No data to save")
        return

    with file_lock:
        df = pd.DataFrame(data)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_query = re.sub(r'[^a-zA-Z0-9]', '_', query)[:30]
        filename = f"{folder_name}/{safe_query}_{timestamp}_thread{thread_id}.xlsx"

        df.to_excel(filename, index=False, engine='openpyxl')
        safe_print(f"[Thread-{thread_id}] ✓ Saved {len(df)} records to: {filename}")

def create_output_folder(folder_name):
    """Create output folder if it doesn't exist"""
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
        safe_print(f"✓ Created folder: {folder_name}")
    return folder_name

def scrape_zipcode(zipcode, base_query, folder_name, thread_id=0):
    """Scrape a single zipcode with anti-detection features"""
    query = f"{base_query} {zipcode}"

    safe_print(f"[Thread-{thread_id}] {'='*50}")
    safe_print(f"[Thread-{thread_id}] Starting: '{query}'")
    safe_print(f"[Thread-{thread_id}] {'='*50}")

    driver = None
    start_time = time.time()

    try:
        driver = init_driver(thread_id)

        if not search_query(driver, query, thread_id):
            return {"zipcode": zipcode, "count": 0, "status": "search_failed"}

        scroll_results(driver, max_scrolls=15, thread_id=thread_id)
        data = parse_cards_with_details(driver, thread_id)

        elapsed = time.time() - start_time

        if data:
            safe_query = f"{base_query.replace(' ', '_')}_{zipcode}"
            save_data_to_excel(data, folder_name, safe_query, thread_id)
            safe_print(f"[Thread-{thread_id}] ✓ Completed {zipcode}: {len(data)} records in {elapsed:.1f}s")
            return {"zipcode": zipcode, "count": len(data), "status": "success", "time": elapsed}
        else:
            safe_print(f"[Thread-{thread_id}] ⚠ No data for {zipcode} ({elapsed:.1f}s)")
            return {"zipcode": zipcode, "count": 0, "status": "no_data", "time": elapsed}

    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"[Thread-{thread_id}] Error with {zipcode}: {e}")
        return {"zipcode": zipcode, "count": 0, "status": "error", "error": str(e), "time": elapsed}

    finally:
        if driver:
            try:
                driver.quit()
                time.sleep(0.5)
            except:
                pass

def main():
    """Main execution function"""
    print("=" * 70)
    print(" GOOGLE MAPS SCRAPER - ZIPCODE ITERATOR")
    print("=" * 70)
    print("Features: Anti-Detection | Rate Limiting | Human Behavior | Multi-Threading")
    print("=" * 70)

    base_query = input("\nEnter search keywords (e.g., 'attorneys'): ").strip()
    if not base_query:
        print("\n✗ Error: Search keywords cannot be empty!")
        return

    excel_path = input("\nEnter Excel file path: ").strip()
    if not os.path.exists(excel_path):
        print(f"\n✗ Error: File not found: {excel_path}")
        return

    # Read Excel with dtype=str to preserve leading zeros
    df = pd.read_excel(excel_path, dtype={"DELIVERY ZIPCODE": str})
    df["DELIVERY ZIPCODE"] = df["DELIVERY ZIPCODE"].astype(str).str.zfill(5)
    zipcodes = df["DELIVERY ZIPCODE"].unique().tolist()

    print(f"\n✓ Loaded {len(zipcodes)} unique zipcodes")
    print(f"First few: {', '.join(zipcodes[:5])}")

    folder_name = create_output_folder("google_maps_data")

    # Multi-threaded execution
    max_workers = min(4, len(zipcodes))
    results = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_zip = {
            executor.submit(scrape_zipcode, zipcode, base_query, folder_name, i): zipcode 
            for i, zipcode in enumerate(zipcodes)
        }

        for future in as_completed(future_to_zip):
            result = future.result()
            results.append(result)

    # Summary
    successful = sum(1 for r in results if r["status"] == "success")
    total_records = sum(r.get("count", 0) for r in results)

    print("\n" + "=" * 70)
    print("SCRAPING COMPLETE")
    print("=" * 70)
    print(f"Successful: {successful}/{len(zipcodes)}")
    print(f"Total records: {total_records}")
    print(f"Output folder: {folder_name}/")
    print("=" * 70)

if __name__ == "__main__":
    main()
