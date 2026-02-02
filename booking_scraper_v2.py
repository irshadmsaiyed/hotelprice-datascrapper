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
import time
from datetime import datetime

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
        
        # Find and fill the destination field
        try:
            print("Entering destination...")
            destination_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, "ss"))
            )
            destination_field.clear()
            destination_field.send_keys(f"{hotel_name}, {city}")
            time.sleep(3)
            
            # Close any pop-ups that might appear
            close_all_popups(driver)
            
            # Wait for autocomplete suggestions and click the first one
            try:
                first_suggestion = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "li[data-i='0']"))
                )
                first_suggestion.click()
                print("✓ Destination selected")
                time.sleep(1)
            except:
                # If autocomplete doesn't work, just press Enter
                from selenium.webdriver.common.keys import Keys
                destination_field.send_keys(Keys.RETURN)
                print("✓ Destination entered (pressed Enter)")
                time.sleep(2)
                
        except Exception as e:
            print(f"✗ Error with destination field: {e}")
        
        # Close any pop-ups before date selection
        close_all_popups(driver)
        
        # Handle date selection
        try:
            print("Selecting dates...")
            # Parse dates
            checkin = datetime.strptime(check_in_date, "%Y-%m-%d")
            checkout = datetime.strptime(check_out_date, "%Y-%m-%d")
            
            # Try multiple selectors for date button
            date_button_selectors = [
                "button[data-testid='date-display-field-start']",
                "div[data-testid='searchbox-dates-container']",
                "button.sb-date-field__display",
            ]
            
            date_button = None
            for selector in date_button_selectors:
                try:
                    date_button = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    break
                except:
                    continue
            
            if date_button:
                date_button.click()
                time.sleep(2)
                close_all_popups(driver)
                
                # Select check-in date
                checkin_xpath = f"//span[@data-date='{check_in_date}']"
                try:
                    checkin_element = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, checkin_xpath))
                    )
                    checkin_element.click()
                    time.sleep(1)
                except Exception as e:
                    print(f"Could not click check-in date: {e}")
                
                # Select check-out date
                checkout_xpath = f"//span[@data-date='{check_out_date}']"
                try:
                    checkout_element = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, checkout_xpath))
                    )
                    checkout_element.click()
                    print("✓ Dates selected")
                    time.sleep(1)
                except Exception as e:
                    print(f"Could not click check-out date: {e}")
            
        except Exception as e:
            print(f"✗ Error with date selection: {e}")
        
        # Close pop-ups before clicking search
        close_all_popups(driver)
        
        # Click search button
        try:
            print("Clicking search button...")
            
            # Try multiple selectors for search button
            search_button_selectors = [
                "button[type='submit']",
                "button.sb-searchbox__button",
                "button[data-testid='search-button']",
            ]
            
            search_clicked = False
            for selector in search_button_selectors:
                try:
                    search_button = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    search_button.click()
                    search_clicked = True
                    print("✓ Search initiated")
                    break
                except:
                    continue
            
            if not search_clicked:
                print("✗ Could not click search button")
                
            time.sleep(5)
            
        except Exception as e:
            print(f"✗ Error clicking search button: {e}")
        
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
        
        for idx, hotel in enumerate(hotels[:10], 1):  # Check first 10 results
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
    hotel_name = "Al Khoory Skygarden Hotel"
    check_in_date = "2026-06-09"
    check_out_date = "2026-06-10"

    scrape_booking_price(city, hotel_name, check_in_date, check_out_date)


if __name__ == "__main__":
    main()

