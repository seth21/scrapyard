import undetected_chromedriver as uc
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
from urllib.parse import urljoin

from model.context import Context


class SeleniumDriver:
    def __init__(self, headless=True):
        self.driver = None
        self._headless = headless
        self.start_driver(headless)

    def is_headless(self):
        return self._headless

    def start_driver(self, headless=True):
        if not self.driver:
            options = Options()
            options.add_argument("--window-size=1920,1080")
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")

            driver_path = ChromeDriverManager().install()
            self.driver = uc.Chrome(options=options, headless=headless, driver_executable_path=driver_path)

    def stop_driver(self):
        if self.driver:
            try:
                self.driver.quit()
            finally:
                self.driver = None

    def switch_to_visible(self):
        if self.driver and self._headless:
            self.stop_driver()
            self._headless = False
            self.start_driver(headless=False)

    def switch_to_headless(self):
        if self.driver and not self._headless:
            self.stop_driver()
            self._headless = True
            self.start_driver(headless=True)

    def _wait_for_dom_stability(self, drv, timeout=5, interval=0.5):
        end_time = time.time() + timeout
        last_length = 0

        while time.time() < end_time:
            html = drv.page_source
            if len(html) == last_length:
                return True
            last_length = len(html)
            time.sleep(interval)
        return False

    def visit_page(self, base_url: str, ctx:Context, wait_time=2) -> str:
        if not base_url:
            ctx.push_message("error", "All fields are required!")
            return None
        if ctx.stop_event.is_set():
            return None
        ctx.push_message("info:", f"--- Visiting {base_url} ---")

        try:
            self.driver.get(base_url)
            ctx.push_message("info", f"Page loaded, waiting for JS to render...")

            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            self._wait_for_dom_stability(self.driver)

            html = self.driver.page_source
            return html
        except Exception as e:
            ctx.push_message("error", f"Selenium error: {e}")
            return None


    def extract_page_data_from_soup(self, current_soup:BeautifulSoup, base_url, data_selector, ctx:Context, link_mode=False, max_data=250):
        # Parse HTML
        soup = current_soup
        data_elements = []
        try:
            # Use CSS Selector to find links
            data_elements = soup.select(data_selector)
        except Exception as e:
            ctx.push_message("error", f"Beautiful Soup error: {e}")

        data = []  # Clear old data

        if not data_elements:
            ctx.push_message("error", "No data found matching criteria.")
        else:
            ctx.push_message("info", f"Found {len(data_elements)} data points.")
            for i, el in enumerate(data_elements):
                if i >= max_data:
                    break
                if link_mode:
                    # Handle <a> tags directly, or find <a> inside the selected element
                    if el.name == 'a':
                        href = el.get('href')
                    else:
                        a_tag = el.find('a')
                        href = a_tag.get('href') if a_tag else None
                    if href:
                        # Convert relative URL (/title/tt123) to absolute (https://imdb.../title/tt123)
                        full_url = urljoin(base_url, href)
                        if full_url not in data:
                            data.append(full_url)
                            ctx.push_message("info", f"[URL added #{i}] {full_url}")
                else:
                    extracted_text = el.get_text(strip=True)
                    if extracted_text:
                        data.append({
                            "Source URL": base_url,
                            "Extracted Data": extracted_text  # Limit length for Excel
                        })
                        ctx.push_message("info", f"[Data added #{i}] {base_url} : {extracted_text}")
                    else:
                        ctx.push_message("warning", f"[No data found on this page. #{i}] {base_url}")
        return data


    def extract_page_data_from_html(self, html:str, base_url, data_selector, ctx:Context, link_mode=False, max_data=250):
        # Parse HTML
        soup = BeautifulSoup(html, 'html.parser')
        data_elements = []
        try:
            # Use CSS Selector to find links
            data_elements = soup.select(data_selector)
        except Exception as e:
            ctx.push_message("error", f"Beautiful Soup error: {e}")

        data = []  # Clear old data

        if not data_elements:
            ctx.push_message("error", "No data found matching criteria.")
        else:
            ctx.push_message("info", f"Found {len(data_elements)} data points.")
            for i, el in enumerate(data_elements):
                if i >= max_data:
                    break
                if link_mode:
                    # Handle <a> tags directly, or find <a> inside the selected element
                    if el.name == 'a':
                        href = el.get('href')
                    else:
                        a_tag = el.find('a')
                        href = a_tag.get('href') if a_tag else None
                    if href:
                        # Convert relative URL (/title/tt123) to absolute (https://imdb.../title/tt123)
                        full_url = urljoin(base_url, href)
                        if full_url not in data:
                            data.append(full_url)
                            ctx.push_message("info", f"[URL added #{i}] {full_url}")
                else:
                    extracted_text = el.get_text(strip=True)
                    if extracted_text:
                        data.append({
                            "Source URL": base_url,
                            "Extracted Data": extracted_text  # Limit length for Excel
                        })
                        ctx.push_message("info", f"[Data added #{i}] {base_url} : {extracted_text}")
                    else:
                        ctx.push_message("warning", f"[No data found on this page. #{i}] {base_url}")
        return data