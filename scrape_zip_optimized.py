#!/usr/bin/env python3
"""
Multi-Threaded Google Maps Scraper
Optimized for 4 vCPU + 16GB RAM Hostinger VPS
Author: Auto-generated
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
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from queue import Queue
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

def safe_print(message):
    """Thread-safe printing"""
    with print_lock:
        print(message)
        logger.info(message)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
]

def get_chrome_version():
    """Get Chrome version - Ubuntu 24.04 compatible"""
    try:
        import subprocess
        result = subprocess.run(['google-chrome', '--version'], 
                              capture_output=True, text=True, timeout=5)
        version = result.stdout.strip().split()[-1].split('.')[0]
        logger.info(f"Chrome version detected: {version}")
        return int(version)
    except Exception as e:
        logger.warning(f"Could not detect Chrome version: {e}")
        return None

def human_delay(min_sec=0.8, max_sec=1.5):
    """Human-like delay with reduced wait times"""
    time.sleep(random.uniform(min_sec, max_sec))

def init_driver(thread_id=0):
    """Initialize Chrome driver optimized for multi-threading"""
    safe_print(f"[Thread-{thread_id}] Initializing browser...")

    options = uc.ChromeOptions()

    # Essential arguments
    options.add_argument('--headless=new')
    options.add_argument(f'user-agent={random.choice(USER_AGENTS)}')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--disable-notifications')
    options.add_argument('--disable-popup-blocking')

    # Performance optimizations
    options.add_argument('--disable-extensions')
    options.add_argument('--disable-images')
    options.add_argument('--blink-settings=imagesEnabled=false')
    options.add_argument('--disable-logging')
    options.add_argument('--log-level=3')
    options.add_argument('--silent')

    # Memory optimizations
    options.add_argument('--disable-backgrounding-occluded-windows')
    options.add_argument('--disable-background-timer-throttling')
    options.add_argument('--disable-renderer-backgrounding')
    options.add_argument('--disable-features=TranslateUI')
    options.add_argument('--disable-features=BlinkGenPropertyTrees')

    # Additional stability
    options.add_argument('--disable-software-rasterizer')
    options.add_argument('--disable-plugins')

    # Preferences
    prefs = {
        "profile.managed_default_content_settings.images": 2,
        "profile.default_content_setting_values.notifications": 2,
        "profile.managed_default_content_settings.stylesheets": 2,
        "profile.managed_default_content_settings.cookies": 1,
        "profile.managed_default_content_settings.javascript": 1,
        "profile.managed_default_content_settings.plugins": 2,
        "profile.managed_default_content_settings.popups": 2,
        "profile.managed_default_content_settings.geolocation": 2,
        "profile.managed_default_content_settings.media_stream": 2,
    }
    options.add_experimental_option("prefs", prefs)

    chrome_version = get_chrome_version()

    try:
        if chrome_version:
            driver = uc.Chrome(options=options, version_main=chrome_version, use_subprocess=True)
        else:
            driver = uc.Chrome(options=options, use_subprocess=True)

        driver.set_page_load_timeout(30)
        safe_print(f"[Thread-{thread_id}] ✓ Browser initialized!")
        return driver
    except Exception as e:
        logger.error(f"[Thread-{thread_id}] Error initializing driver: {e}")
        raise

def search_query(driver, query: str, thread_id=0):
    """Execute search with optimized delays"""
    try:
        driver.get("https://www.google.com/maps")
        human_delay(2, 3)

        search_box = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, "searchboxinput"))
        )
        search_box.clear()
        time.sleep(0.3)

        # Type search query
        for char in query:
            search_box.send_keys(char)
            time.sleep(random.uniform(0.05, 0.1))

        time.sleep(0.5)
        search_box.send_keys(Keys.ENTER)

        human_delay(3, 4)
        safe_print(f"[Thread-{thread_id}] ✓ Searched: {query}")
        return True
    except Exception as e:
        logger.error(f"[Thread-{thread_id}] Search error: {e}")
        return False

def scroll_results(driver, max_scrolls=10, thread_id=0):
    """Enhanced scrolling with multiple fallback methods"""
    safe_print(f"[Thread-{thread_id}] Scrolling results...")
    
    try:
        time.sleep(2)
        previous_height = 0
        scroll_count = 0
        no_change_count = 0
        
        for i in range(max_scrolls):
            try:
                # Method 1: Scroll window instead of element
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(1)
                
                # Method 2: Send PAGE_DOWN key
                body = driver.find_element(By.TAG_NAME, 'body')
                body.send_keys(Keys.PAGE_DOWN)
                time.sleep(1)
                
                # Method 3: Re-find feed element each time (avoid stale)
                try:
                    scrollable = driver.find_element(By.CSS_SELECTOR, 'div[role="feed"]')
                    driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scrollable)
                except:
                    pass
                
                time.sleep(random.uniform(1.2, 1.8))
                
                # Check progress
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == previous_height:
                    no_change_count += 1
                    if no_change_count >= 3:
                        break
                else:
                    no_change_count = 0
                previous_height = new_height
                scroll_count += 1
                
            except Exception as e:
                logger.warning(f"[Thread-{thread_id}] Scroll iteration {i} error: {e}")
                continue
        
        safe_print(f"[Thread-{thread_id}] Scrolled {scroll_count} times")
        return True
        
    except Exception as e:
        logger.error(f"[Thread-{thread_id}] Scroll error: {e}")
        return False


def extract_business_details(driver, card, index, thread_id=0):
    """Extract business details with robust error handling"""
    try:
        # Scroll card into view
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", card)
        time.sleep(0.3)

        # Click card
        card.click()
        time.sleep(random.uniform(1.5, 2))

        # Extract name
        name = ""
        try:
            name = driver.find_element(By.CSS_SELECTOR, "h1.DUwDvf").text
        except:
            try:
                name = driver.find_element(By.CSS_SELECTOR, "h1.fontHeadlineLarge").text
            except:
                pass

        # Extract rating
        rating = ""
        reviews = ""
        try:
            rating_element = driver.find_element(By.CSS_SELECTOR, "span.ceNzKf")
            rating_text = rating_element.get_attribute("aria-label")
            parts = rating_text.split()
            rating = parts[0]
            if len(parts) > 2:
                reviews = parts[2]
        except:
            pass

        # Extract location/address
        location = ""
        try:
            location = driver.find_element(By.CSS_SELECTOR, "button[data-item-id='address']").get_attribute("aria-label")
            location = location.replace("Address: ", "").strip()
        except:
            pass

        # Extract phone
        phone = ""
        try:
            phone = driver.find_element(By.CSS_SELECTOR, "button[data-item-id^='phone:tel:']").get_attribute("aria-label")
            phone = phone.replace("Phone: ", "").strip()
        except:
            pass

        # Extract website
        website = ""
        try:
            website = driver.find_element(By.CSS_SELECTOR, "a[data-item-id='authority']").get_attribute("href")
        except:
            pass

        # Extract business type/category
        category = ""
        try:
            category = driver.find_element(By.CSS_SELECTOR, "button[jsaction*='category']").text
        except:
            pass

        # Extract hours
        hours = ""
        try:
            hours_element = driver.find_element(By.CSS_SELECTOR, "button[data-item-id='oh']")
            hours = hours_element.get_attribute("aria-label")
        except:
            pass

        return {
            "Name": name,
            "Location": location,
            "Phone Number": phone,
            "Email Address": "",
            "Rating": rating,
            "Reviews": reviews,
            "Website": website,
            "Category": category,
            "Hours": hours
        }
    except Exception as e:
        logger.warning(f"[Thread-{thread_id}] Card {index} extraction error: {e}")
        return None

def parse_cards_with_details(driver, thread_id=0):
    """Parse all business cards with smart rate limiting"""
    safe_print(f"[Thread-{thread_id}] Extracting business data...")

    try:
        feed_container = driver.find_element(By.CSS_SELECTOR, 'div[role="feed"]')
        time.sleep(1)

        cards = feed_container.find_elements(By.CSS_SELECTOR, "div.Nv2PK")
        total_cards = len(cards)

        safe_print(f"[Thread-{thread_id}] ✓ Found {total_cards} listings")

        if total_cards == 0:
            return []

        data = []
        request_count = 0
        start_time = time.time()

        for idx, card in enumerate(cards):
            try:
                # Smart rate limiting: every 5 requests
                if request_count >= 5:
                    elapsed = time.time() - start_time
                    if elapsed < 25:
                        wait_time = 25 - elapsed
                        safe_print(f"[Thread-{thread_id}] ⏸ Rate limit cooldown: {wait_time:.1f}s")
                        time.sleep(wait_time)
                    request_count = 0
                    start_time = time.time()

                details = extract_business_details(driver, card, idx + 1, thread_id)

                if details and details.get("Name"):
                    data.append(details)
                    safe_print(f"[Thread-{thread_id}] ✓ [{idx + 1}/{total_cards}]: {details['Name'][:50]}")
                else:
                    safe_print(f"[Thread-{thread_id}] ⚠ [{idx + 1}/{total_cards}]: No name found")

                request_count += 1
                time.sleep(random.uniform(0.5, 1))

            except Exception as e:
                logger.warning(f"[Thread-{thread_id}] Error processing card {idx + 1}: {e}")
                continue

        safe_print(f"[Thread-{thread_id}] ✓ Successfully extracted {len(data)}/{total_cards} businesses")
        return data

    except Exception as e:
        logger.error(f"[Thread-{thread_id}] Parse error: {e}")
        return []

def scrape_zipcode(zipcode, base_query, folder_name, thread_id=0):
    """Extract initial visible results - NO scrolling required"""
    query = f"{base_query} {zipcode}"
    
    safe_print(f"[Thread-{thread_id}] {'='*50}")
    safe_print(f"[Thread-{thread_id}] Starting: '{query}'")
    safe_print(f"[Thread-{thread_id}] {'='*50}")
    
    driver = None
    start_time = time.time()
    
    try:
        driver = init_driver(thread_id)
        
        # Search
        if not search_query(driver, query, thread_id):
            return {"zipcode": zipcode, "count": 0, "status": "search_failed"}
        
        # Wait longer for all initial results to load
        safe_print(f"[Thread-{thread_id}] Waiting for results...")
        time.sleep(8)  # Give page time to fully render
        
        # Extract visible results (10-20 businesses)
        data = parse_cards_with_details(driver, thread_id)
        
        elapsed = time.time() - start_time
        
        if data:
            safe_query = f"{base_query.replace(' ', '_')}_{zipcode}"
            save_data_to_excel(data, folder_name, safe_query, thread_id)
            safe_print(f"[Thread-{thread_id}] ✓ Completed {zipcode}: {len(data)} records in {elapsed:.1f}s")
            return {"zipcode": zipcode, "count": len(data), "status": "success", "time": elapsed}
        else:
            safe_print(f"[Thread-{thread_id}] ⚠ No data for {zipcode}")
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


def save_data_to_excel(data, folder_name, query, thread_id=0):
    """Thread-safe Excel file saving"""
    if not data:
        return

    with file_lock:
        try:
            df = pd.DataFrame(data)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_query = re.sub(r'[^a-zA-Z0-9_]', '_', query)[:40]
            filename = f"{folder_name}/{safe_query}_{timestamp}_thread{thread_id}.xlsx"

            df.to_excel(filename, index=False, engine='openpyxl')
            safe_print(f"[Thread-{thread_id}] ✓ Saved {len(df)} records to {filename}")
        except Exception as e:
            logger.error(f"[Thread-{thread_id}] Error saving file: {e}")

def create_output_folder():
    """Create output folder - Docker and local compatible"""
    # Try Docker path first
    folder_name = "/app/output"

    # Fallback for local testing
    if not os.path.exists("/app"):
        folder_name = "google_maps_data"

    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
        print(f"✓ Created folder: {folder_name}")
    else:
        print(f"✓ Using folder: {folder_name}")

    return folder_name

def generate_summary_report(results, folder_name, start_time):
    """Generate execution summary report"""
    total_time = time.time() - start_time

    successful = [r for r in results if r["status"] == "success"]
    failed = [r for r in results if r["status"] in ["error", "search_failed", "scroll_failed"]]
    no_data = [r for r in results if r["status"] == "no_data"]

    total_records = sum([r.get("count", 0) for r in results])
    avg_time = sum([r.get("time", 0) for r in results]) / len(results) if results else 0

    report = f"""
{'='*70}
SCRAPING EXECUTION SUMMARY
{'='*70}
Start Time: {datetime.fromtimestamp(start_time).strftime('%Y-%m-%d %H:%M:%S')}
End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Total Duration: {total_time/60:.2f} minutes ({total_time:.1f} seconds)

STATISTICS:
- Total Zipcodes: {len(results)}
- Successful: {len(successful)} ({len(successful)/len(results)*100:.1f}%)
- Failed: {len(failed)} ({len(failed)/len(results)*100:.1f}%)
- No Data: {len(no_data)} ({len(no_data)/len(results)*100:.1f}%)

DATA EXTRACTED:
- Total Records: {total_records}
- Average per Zipcode: {total_records/len(successful) if successful else 0:.1f}
- Average Time per Zipcode: {avg_time:.1f} seconds

PERFORMANCE:
- Records per Minute: {total_records/(total_time/60):.1f}
- Zipcodes per Hour: {len(results)/(total_time/3600):.1f}

OUTPUT LOCATION:
- {folder_name}

FAILED ZIPCODES:
{chr(10).join([f"  - {r['zipcode']}: {r.get('error', r['status'])}" for r in failed]) if failed else "  None"}
{'='*70}
"""

    # Save report
    report_file = f"{folder_name}/summary_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(report_file, 'w') as f:
        f.write(report)

    print(report)
    logger.info(f"Summary report saved to {report_file}")

def main():
    """Main execution function"""
    print("=" * 70)
    print(" MULTI-THREADED GOOGLE MAPS SCRAPER")
    print(" Optimized for Hostinger VPS (4 vCPU + 16GB RAM)")
    print("=" * 70)
    print(" Features:")
    print("  • Parallel Processing (3 threads)")
    print("  • Intelligent Rate Limiting")
    print("  • Comprehensive Error Handling")
    print("  • 3-4x Faster than Sequential")
    print("=" * 70)

    # Get search parameters
    base_query = input("\nEnter base search keywords (e.g., 'attorneys in'): ").strip()
    if not base_query:
        print("\n✗ Error: Search keywords cannot be empty!")
        return

    # Get Excel file path
    excel_path = input("\nEnter Excel file path (or press Enter for default): ").strip()
    if not excel_path:
        excel_path = "/app/excel_files/Book1.xlsx"

    if not os.path.exists(excel_path):
        print(f"\n✗ Error: File not found: {excel_path}")
        return

    # Read zipcodes
    try:
        df = pd.read_excel(excel_path, dtype={"DELIVERY ZIPCODE": str})

        # Handle zipcode column name variations
        zipcode_column = None
        for col in df.columns:
            if 'zip' in col.lower():
                zipcode_column = col
                break

        if not zipcode_column:
            print("\n✗ Error: No zipcode column found in Excel file")
            return

        df[zipcode_column] = df[zipcode_column].astype(str).str.zfill(5)
        zipcodes = df[zipcode_column].unique().tolist()

        print(f"\n✓ Loaded {len(zipcodes)} unique zipcodes from '{zipcode_column}'")
        print(f"✓ First 5: {', '.join(zipcodes[:5])}")
        if len(zipcodes) > 5:
            print(f"✓ Last 5: {', '.join(zipcodes[-5:])}")
    except Exception as e:
        print(f"\n✗ Error reading Excel file: {e}")
        return

    folder_name = create_output_folder()

    # Multi-threading configuration
    MAX_WORKERS = 3
    print(f"\n✓ Configuration: {MAX_WORKERS} parallel workers")
    print(f"✓ Estimated time: {len(zipcodes) * 25 / MAX_WORKERS / 60:.1f} minutes")
    print("\n" + "=" * 70)
    print("Starting scraping process...")
    print("=" * 70 + "\n")

    start_time = time.time()
    results = []

    # Execute parallel scraping
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_zipcode = {
            executor.submit(scrape_zipcode, zipcode, base_query, folder_name, i % MAX_WORKERS): zipcode 
            for i, zipcode in enumerate(zipcodes)
        }

        completed = 0
        for future in as_completed(future_to_zipcode):
            zipcode = future_to_zipcode[future]
            completed += 1
            try:
                result = future.result()
                results.append(result)

                progress = (completed / len(zipcodes)) * 100
                safe_print(f"\n{'='*70}")
                safe_print(f"PROGRESS: {completed}/{len(zipcodes)} ({progress:.1f}%) | "
                          f"Status: {result['status']} | Records: {result.get('count', 0)}")
                safe_print(f"{'='*70}\n")

            except Exception as e:
                logger.error(f"Exception for {zipcode}: {e}")
                results.append({"zipcode": zipcode, "status": "exception", "error": str(e)})

    # Generate summary
    generate_summary_report(results, folder_name, start_time)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n✗ Scraping interrupted by user")
        logger.info("Scraping interrupted by user")
    except Exception as e:
        print(f"\n\n✗ Fatal error: {e}")
        logger.error(f"Fatal error: {e}", exc_info=True)
