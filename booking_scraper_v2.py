"""
Booking.com Hotel Price Scraper using Selenium (with Pop-up Handling)
This script searches for hotel prices on Booking.com for a specific city and hotel

INSTALLATION:
1. uv pip install selenium webdriver-manager
2. Run this script: uv run booking_scraper_popup_handler.py
"""

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import time
import random
from datetime import datetime


def human_type(driver, element, text, min_delay=0.05, max_delay=0.35):
    """
    Types text character by character with random delays between each
    keystroke to simulate real human typing behaviour.

    Parameters:
    - driver     : Selenium WebDriver instance
    - element    : the input element to type into
    - text       : the full string to type
    - min_delay  : shortest pause (seconds) between two keystrokes
    - max_delay  : longest  pause (seconds) between two keystrokes
    """
    element.click()                          # focus the field first
    time.sleep(random.uniform(0.3, 0.7))     # small pause after click, like a human

    for char in text:
        element.send_keys(char)
        # random pause between each character  →  looks natural
        time.sleep(random.uniform(min_delay, max_delay))

        # occasionally add a slightly longer pause (like a human thinking)
        if random.random() < 0.15:           # 15 % chance
            time.sleep(random.uniform(0.4, 0.9))

    print(f'   ✓ Typed  →  "{text}"')


def wait_for_suggestions(driver, timeout=8):
    """
    Waits until the autocomplete dropdown appears and returns
    the list of <li> suggestion elements.  Returns an empty list
    when the dropdown does not appear within *timeout* seconds.
    """
    suggestion_selectors = [
        "li[data-i]",                                          # indexed items
        "ul[role='listbox'] li",                               # ARIA listbox
        "div[data-testid='autocomplete-results'] li",                  # testid variant
        ".suggestions-list li",                                # class variant
    ]
    for sel in suggestion_selectors:
        try:
            items = WebDriverWait(driver, timeout).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, sel))
            )
            if items:
                print(f"   ✓ Found {len(items)} autocomplete suggestion(s)")
                return items
        except (TimeoutException, NoSuchElementException):
            continue
    return []


def pick_best_suggestion(suggestions, hotel_name):
    """
    From the list of autocomplete <li> elements pick the one whose
    visible text best matches *hotel_name*.  Falls back to the first
    suggestion when no good match is found.

    Returns the chosen element (or None if the list is empty).
    """
    if not suggestions:
        return None

    hotel_lower = hotel_name.lower()
    # score every suggestion by how many words from hotel_name it contains
    scored = []
    for item in suggestions:
        item_text = item.text.strip().lower()
        # count how many words from hotel_name appear in the suggestion
        score = sum(1 for word in hotel_lower.split() if word in item_text)
        scored.append((score, item_text, item))
        print(f'      candidate  →  "{item.text.strip()}"  (score {score})')

    scored.sort(key=lambda x: x[0], reverse=True)
    best = scored[0]
    print(f'   ✓ Best match  →  "{best[1]}"')
    return best[2]

def close_all_popups(driver):
    """
    Close all common pop-ups on Booking.com
    """
    popup_closed = False
    
    # List of common pop-up close button selectors
    popup_selectors = [
        # Cookie consent
        "button[id='onetrust-accept-btn-handler']",
        "button[aria-label='Dismiss sign-in info.']",
        
        # Sign-in pop-ups
        "button[aria-label='Dismiss sign in information.']",
        "button[aria-label='Close']",
        "button.fc63351294.a822bdf511.e3c025e003.fa565176a8.f7db01295e.c334e6f658.e1b7cfea84.cd7aa7c891",
        
        # Generic close buttons
        "button[data-testid='header-sign-in-button'] ~ button",
        "div[role='dialog'] button[aria-label='Close']",
        "button.a83ed08757.c21c56c305.bf0537ecb5.ab98298258.deab83296e.f4552b6561",
        
        # X buttons
        "button.bui-modal__close",
        "button.modal-mask-closeBtn",
        
        # Overlay close
        "div.bui-overlay",
        
        # Sign-in modal
        "button[aria-label='Dismiss sign-in info.']",
        "div[data-testid='header-sign-in-button']",
        
        # Genius loyalty program
        "button[aria-label='Close Genius info']",
    ]
    
    for selector in popup_selectors:
        try:
            close_button = WebDriverWait(driver, 2).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
            )
            close_button.click()
            print(f"✓ Closed pop-up: {selector[:50]}...")
            popup_closed = True
            time.sleep(0.5)
        except (TimeoutException, NoSuchElementException, ElementClickInterceptedException):
            continue
    
    # Try closing by pressing Escape key
    try:
        from selenium.webdriver.common.keys import Keys
        webdriver.ActionChains(driver).send_keys(Keys.ESCAPE).perform()
        time.sleep(0.5)
    except:
        pass
    
    # Click outside any modal (on the backdrop)
    try:
        backdrop = driver.find_element(By.CSS_SELECTOR, "div[class*='modal-mask']")
        backdrop.click()
        popup_closed = True
        time.sleep(0.5)
    except:
        pass
    
    return popup_closed


def scrape_booking_price(city, hotel_name, check_in_date, check_out_date):
    """
    Scrape hotel prices from Booking.com with pop-up handling
    
    Parameters:
    - city: str (e.g., "Dubai")
    - hotel_name: str (e.g., "Al Khoory Skygarden Hotel")
    - check_in_date: str (format: "YYYY-MM-DD", e.g., "2026-06-09")
    - check_out_date: str (format: "YYYY-MM-DD", e.g., "2026-06-10")
    """
    
    # Setup Chrome options
    chrome_options = Options()
    chrome_options.add_argument('--start-maximized')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument('--disable-notifications')
    chrome_options.add_argument('--disable-popup-blocking')
    
    # Add user agent to look more like a real browser
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    # Uncomment the line below to run in headless mode (no browser window)
    # chrome_options.add_argument('--headless')
    
    # Initialize the driver with automatic ChromeDriver installation
    print("Setting up Chrome driver...")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        print(f"\n{'='*80}")
        print(f"SEARCHING FOR HOTEL")
        print(f"{'='*80}")
        print(f"Hotel: {hotel_name}")
        print(f"City: {city}")
        print(f"Check-in: {check_in_date}")
        print(f"Check-out: {check_out_date}")
        print(f"{'='*80}\n")
        
        # Navigate to Booking.com
        print("Opening Booking.com...")
        driver.get("https://www.booking.com")
        time.sleep(3)
        
        # Close initial pop-ups
        print("Checking for pop-ups...")
        close_all_popups(driver)
        
        # ── DESTINATION FIELD  (human-like typing) ────────────────────────
        try:
            print("Entering destination (typing like a human)...\n")

            destination_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "ss"))
            )
            destination_field.clear()
            time.sleep(random.uniform(0.3, 0.6))

            # ── Step 1 : type the hotel name  word by word ──────────────
            words = hotel_name.split()                        # e.g. ["Al","Khoory","Skygarden","Hotel"]
            for i, word in enumerate(words):
                # type each character of the current word
                human_type(driver, destination_field, word)

                # after every word (except the last) add a space
                if i < len(words) - 1:
                    destination_field.send_keys(" ")
                    time.sleep(random.uniform(0.15, 0.4))

                # after the first two words have been typed wait a moment
                # and check whether a useful autocomplete suggestion already
                # appeared  →  if yes, click it immediately and stop typing
                if i >= 1:
                    time.sleep(random.uniform(0.6, 1.2))   # short pause so dropdown can render
                    close_all_popups(driver)
                    suggestions = wait_for_suggestions(driver, timeout=3)
                    best = pick_best_suggestion(suggestions, hotel_name)
                    if best:
                        try:
                            best.click()
                            print("   ✓ Autocomplete suggestion selected  →  done!\n")
                            time.sleep(1)
                            break                            # exit the word-loop
                        except ElementClickInterceptedException:
                            close_all_popups(driver)
                            best.click()
                            print("   ✓ Autocomplete suggestion selected (after pop-up)  →  done!\n")
                            time.sleep(1)
                            break
                else:
                    # after the very first word just wait for suggestions to appear
                    time.sleep(random.uniform(0.8, 1.5))
            else:
                # ── Step 2 : no suggestion was picked during the loop ──
                # wait one more time for suggestions after the full name
                time.sleep(random.uniform(1.0, 2.0))
                close_all_popups(driver)
                suggestions = wait_for_suggestions(driver, timeout=5)
                best = pick_best_suggestion(suggestions, hotel_name)
                if best:
                    try:
                        best.click()
                        print("   ✓ Autocomplete suggestion selected  →  done!\n")
                        time.sleep(1)
                    except ElementClickInterceptedException:
                        close_all_popups(driver)
                        best.click()
                        print("   ✓ Autocomplete suggestion selected (after pop-up)  →  done!\n")
                        time.sleep(1)
                else:
                    # absolute fallback  →  press Enter
                    destination_field.send_keys(Keys.RETURN)
                    print("   ⚠ No suggestion matched  →  pressed Enter instead\n")
                    time.sleep(2)

        except Exception as e:
            print(f"   ✗ Error with destination field: {e}")
        
        # Close any pop-ups before date selection
        close_all_popups(driver)

        # ── DATE SELECTION  (selectors taken from the real HTML) ──────────
        try:
            print("Selecting dates...")
            checkin  = datetime.strptime(check_in_date,  "%Y-%m-%d")
            checkout = datetime.strptime(check_out_date, "%Y-%m-%d")

            # ── Step 1 : open the calendar ────────────────────────────────
            open_selectors = [
                "button[data-testid='date-display-field-start']",
                "div[data-testid='searchbox-dates-container']",
                "button.sb-date-field__display",
                "#calendar-searchboxdatepicker-tab-trigger",   # Calendar tab (seen in HTML)
            ]
            calendar_opened = False
            for sel in open_selectors:
                try:
                    btn = WebDriverWait(driver, 4).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, sel))
                    )
                    btn.click()
                    print(f"   ✓ Calendar opened via  →  {sel}")
                    calendar_opened = True
                    time.sleep(1.5)
                    break
                except (TimeoutException, NoSuchElementException):
                    continue

            if not calendar_opened:
                raise Exception("Could not open the calendar datepicker")

            close_all_popups(driver)

            # ── helper : navigate calendar to the month containing target_date
            def navigate_to_month(target_date: datetime):
                """
                Reads the month titles shown on-screen (h3 aria-live='polite').
                Clicks Previous / Next month until the target month is visible.
                """
                for _ in range(24):                                       # safety cap
                    titles = driver.find_elements(
                        By.CSS_SELECTOR,
                        "div[data-testid='searchbox-datepicker-calendar'] "
                        "h3[aria-live='polite']"
                    )
                    displayed = [t.text.strip() for t in titles]          # ["June 2026", "July 2026"]
                    target_str = target_date.strftime("%B %Y")            # "June 2026"
                    print(f"      visible months  →  {displayed}   |  need  →  {target_str}")

                    if target_str in displayed:
                        print(f"   ✓ Correct month visible  →  {target_str}")
                        return

                    # compare numerically to decide direction
                    first_shown = datetime.strptime(displayed[0], "%B %Y")
                    arrow = "button[aria-label='Previous month']" if target_date < first_shown \
                            else "button[aria-label='Next month']"
                    driver.find_element(By.CSS_SELECTOR, arrow).click()
                    time.sleep(0.8)

                raise Exception(f"Could not navigate to {target_date.strftime('%B %Y')}")

            # ── helper : click a date cell by data-date attribute ─────────
            def click_date(date_str: str):
                """  span[data-date='YYYY-MM-DD']  — confirmed in pasted HTML  """
                el = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable(
                        (By.CSS_SELECTOR, f"span[data-date='{date_str}']")
                    )
                )
                el.click()
                print(f"   ✓ Clicked date  →  {date_str}")
                time.sleep(0.8)

            # ── Step 2 : navigate + click CHECK-IN ────────────────────────
            navigate_to_month(checkin)
            click_date(check_in_date)
            time.sleep(0.5)

            # ── Step 3 : navigate + click CHECK-OUT ───────────────────────
            navigate_to_month(checkout)                                   # view may have shifted
            click_date(check_out_date)
            time.sleep(1.0)
            print("   ✓ Both dates selected")

            # ── Step 4 : click Apply in the datepicker footer ────────────
            # Footer:  div[data-testid='datepicker-footer']
            # Apply is the primary <button> inside it.
            try:
                apply_btn = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((
                        By.CSS_SELECTOR,
                        "div[data-testid='datepicker-footer'] button"
                    ))
                )
                apply_btn.click()
                print("   ✓ Apply button clicked")
                time.sleep(1)
            except (TimeoutException, NoSuchElementException):
                print("   ⚠ No Apply button — assuming calendar auto-closed")

        except Exception as e:
            print(f"   ✗ Error with date selection: {e}")

        # ── Close pop-ups before search ───────────────────────────────────
        close_all_popups(driver)
        time.sleep(0.5)

        # ── SEARCH BUTTON ─────────────────────────────────────────────────
        try:
            print("Clicking search button...")

            search_button_selectors = [
                "button[type='submit']",
                "button.sb-searchbox__button",
                "button[data-testid='search-button']",
            ]

            search_clicked = False
            for sel in search_button_selectors:
                try:
                    search_button = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, sel))
                    )
                    search_button.click()
                    search_clicked = True
                    print("   ✓ Search initiated")
                    break
                except (TimeoutException, NoSuchElementException):
                    continue

            if not search_clicked:
                print("   ✗ Could not click search button")

            time.sleep(5)

        except Exception as e:
            print(f"   ✗ Error clicking search button: {e}")
        
        # Close any pop-ups on results page
        print("Checking for pop-ups on results page...")
        time.sleep(2)
        close_all_popups(driver)
        time.sleep(1)
        close_all_popups(driver)  # Try twice
        
        # Wait for results to load
        print("Loading results...\n")
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='property-card']"))
            )
        except TimeoutException:
            print("⚠️  Results took too long to load or no results found")
            print("Current URL:", driver.current_url)
            time.sleep(5)
        
        # Close pop-ups one more time before extracting data
        close_all_popups(driver)
        
        # Extract hotel information
        print(f"\n{'='*80}")
        print("SEARCH RESULTS")
        print(f"{'='*80}\n")
        
        # Try to find hotel cards
        try:
            hotels = driver.find_elements(By.CSS_SELECTOR, "[data-testid='property-card']")
            
            if len(hotels) == 0:
                print("⚠️  No hotel cards found. Trying alternative selector...")
                hotels = driver.find_elements(By.CSS_SELECTOR, "div[data-testid='property-card']")
            
            if len(hotels) == 0:
                print("⚠️  Still no results. The page structure might have changed.")
                print("Current URL:", driver.current_url)
                print("\nWaiting 20 seconds so you can inspect the page...")
                time.sleep(20)
                return
            
            print(f"Found {len(hotels)} hotel(s)\n")
            
        except Exception as e:
            print(f"Error finding hotel elements: {e}")
            hotels = []
        
        found_target_hotel = False
        
        for idx, hotel in enumerate(hotels[:2], 1):  # Check first 10 results
            try:
                # Get hotel name
                name_element = hotel.find_element(By.CSS_SELECTOR, "[data-testid='title']")
                name = name_element.text
                
                # Get price
                try:
                    price_element = hotel.find_element(By.CSS_SELECTOR, "[data-testid='price-and-discounted-price']")
                    price = price_element.text
                except:
                    try:
                        price_element = hotel.find_element(By.CSS_SELECTOR, ".prco-valign-middle-helper")
                        price = price_element.text
                    except:
                        try:
                            price_element = hotel.find_element(By.CSS_SELECTOR, "span[data-testid='price-and-discounted-price']")
                            price = price_element.text
                        except:
                            price = "Price not available"
                
                # Get rating if available
                try:
                    rating_element = hotel.find_element(By.CSS_SELECTOR, "[data-testid='review-score'] div")
                    rating = rating_element.text
                except:
                    rating = "No rating"
                
                # Get location/address if available
                try:
                    location_element = hotel.find_element(By.CSS_SELECTOR, "[data-testid='address']")
                    location = location_element.text
                except:
                    location = "Location not specified"
                
                print(f"{idx}. {name}")
                print(f"   Price: {price}")
                print(f"   Rating: {rating}")
                print(f"   Location: {location}")
                
                # Check if this is the target hotel
                if hotel_name.lower() in name.lower():
                    found_target_hotel = True
                    print(f"\n   🎯 TARGET HOTEL FOUND! 🎯")
                
                print(f"   {'-'*76}")
                
            except Exception as e:
                print(f"✗ Error extracting data for hotel {idx}: {e}")
        
        if not found_target_hotel:
            print(f"\n⚠️  WARNING: '{hotel_name}' was not found in the first 10 results.")
            print("   Possible reasons:")
            print("   - Hotel name might be different on Booking.com")
            print("   - Hotel might be listed further down")
            print("   - Hotel might not be available for selected dates")
            print("   - Hotel might not be on Booking.com\n")
        
        print(f"{'='*80}\n")
        
        # Keep browser open for inspection
        print("Browser will remain open for 20 seconds for you to inspect...")
        print("You can also scroll through the results manually.")
        time.sleep(20)
        
    except Exception as e:
        print(f"\n✗ An error occurred: {e}")
        print("The browser will remain open for 15 seconds so you can see what happened...")
        time.sleep(15)
        
    finally:
        driver.quit()
        print("\n✓ Browser closed.")
        print("Script completed!")


def main():
    print("\n" + "="*80)
    print("BOOKING.COM HOTEL PRICE SCRAPER")
    print("="*80 + "\n")

    city = "Dubai"
    #hotel_name = "Al Khoory Skygarden Hotel"
    hotel_name = "Howard Johnson Bur Dubai"
    check_in_date = "2026-05-01"
    check_out_date = "2026-05-05"

    scrape_booking_price(city, hotel_name, check_in_date, check_out_date)


if __name__ == "__main__":
    main()

