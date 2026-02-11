import json
import csv
import time
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager

class WebScraper:
    def __init__(self, headless=True):
        """
        Initializes the Selenium WebDriver with Chrome options.
        """
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Initialize the driver using webdriver-manager
        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)
        self.data = []

    def login(self, url, username, password):
        """
        Handles automated login.
        """
        print(f"Logging in to {url}...")
        try:
            self.driver.get(url)
            
            # Wait for login fields and enter credentials
            user_field = self.wait.until(EC.presence_of_element_located((By.ID, "username")))
            pass_field = self.driver.find_element(By.ID, "password")
            
            user_field.send_keys(username)
            pass_field.send_keys(password)
            
            # Submit the form
            login_button = self.driver.find_element(By.CSS_SELECTOR, 'input[type="submit"]')
            login_button.click()
            
            # Verify login success (checking for logout link)
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'a[href="/logout"]')))
            print("Login successful!")
            return True
        except (TimeoutException, NoSuchElementException) as e:
            print(f"Login failed: {e}")
            return False

    def scrape_quotes(self, url):
        """
        Navigates to the dynamic page and extracts data.
        Uses Selenium to load the page and BeautifulSoup to parse the HTML.
        """
        print(f"Scraping data from {url}...")
        try:
            self.driver.get(url)
            
            # Wait for the dynamic content to load (quotes are loaded via JS)
            self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "quote")))
            
            # Get the page source and parse with BeautifulSoup
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            quotes = soup.find_all('div', class_='quote')
            
            for quote in quotes:
                text = quote.find('span', class_='text').get_text(strip=True)
                author = quote.find('small', class_='author').get_text(strip=True)
                tags = [tag.get_text(strip=True) for tag in quote.find_all('a', class_='tag')]
                
                self.data.append({
                    'text': text,
                    'author': author,
                    'tags': ', '.join(tags)
                })
            
            print(f"Successfully scraped {len(quotes)} quotes.")
        except TimeoutException:
            print("Timed out waiting for page to load.")
        except Exception as e:
            print(f"An error occurred during scraping: {e}")

    def save_data(self, base_filename):
        """
        Stores results in CSV and JSON format using Pandas.
        """
        if not self.data:
            print("No data to save.")
            return

        df = pd.DataFrame(self.data)
        
        # Save to CSV
        csv_file = f"{base_filename}.csv"
        df.to_csv(csv_file, index=False)
        print(f"Data saved to {csv_file}")
        
        # Save to JSON
        json_file = f"{base_filename}.json"
        df.to_json(json_file, orient='records', indent=4)
        print(f"Data saved to {json_file}")

    def close(self):
        """
        Closes the WebDriver.
        """
        if self.driver:
            self.driver.quit()

if __name__ == "__main__":
    scraper = WebScraper(headless=True)
    try:
        # 1. Automated Login (using a demo site)
        # Note: In a real scenario, use environment variables for credentials
        login_url = "https://quotes.toscrape.com/login"
        scraper.login(login_url, "test_user", "test_password")
        
        # 2. Navigation & Data Extraction from dynamic content
        dynamic_url = "https://quotes.toscrape.com/js/"
        scraper.scrape_quotes(dynamic_url)
        
        # 3. Store results in CSV/JSON
        scraper.save_data("scraped_quotes")
        
    finally:
        # Ensure driver is closed even if errors occur
        scraper.close()
