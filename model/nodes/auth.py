import os
import pickle
import time
from urllib.parse import urlparse
import tkinter as tk
from tkinter import messagebox
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from model.nodes.base import BaseNode
from model.nodes.registry import register_node


@register_node("ensure_auth")
class EnsureAuthNode(BaseNode):

    def execute(self, step_config, context, browser, engine, context_soup=None, inherited_data=None):
        login_url = step_config.get('login_url', '')
        success_selector = step_config.get('success_selector', '')
        cookie_name = step_config.get('cookie_name', '')

        target_url = login_url if login_url else engine.current_url if hasattr(engine, 'current_url') else None
        if not target_url:
            context.push_message("error", "EnsureAuth: No URL available for authentication")
            return None

        target_url = target_url.strip()
        if not target_url:
            context.push_message("error", "EnsureAuth: Login URL is empty")
            return None

        domain = self._extract_domain(target_url)
        if cookie_name and cookie_name.strip():
            cookie_file = os.path.join("cookies", f"{cookie_name.strip()}.pkl")
        else:
            cookie_file = os.path.join("cookies", f"{domain}.pkl")

        context.push_message("info", f"EnsureAuth: Checking authentication for {domain}")

        cookies_loaded = self._try_load_cookies(browser, cookie_file, context)

        browser.visit_page(target_url, context)
        time.sleep(1)

        auth_valid = self._check_auth_valid(browser, success_selector, context)

        if auth_valid:
            context.push_message("info", "EnsureAuth: Existing session is valid")
            return None

        if not success_selector and cookies_loaded:
            context.push_message("info", "EnsureAuth: No success selector configured, switching to visible to verify...")
            if browser.is_headless():
                context.push_message("info", "EnsureAuth: Switching to visible browser for verification")
                browser.switch_to_visible()
                browser.visit_page(target_url, context)
                time.sleep(0.5)
                self._try_load_cookies(browser, cookie_file, context)
                browser.visit_page(target_url, context)
            context.push_message("info", "EnsureAuth: Please verify login status in the browser")
            if self._ask_user_auth_status(context):
                context.push_message("info", "EnsureAuth: User confirmed already logged in")
                context.push_message("info", "EnsureAuth: Switching back to headless mode")
                browser.switch_to_headless()
                browser.visit_page(target_url, context)
                time.sleep(0.5)
                self._try_load_cookies(browser, cookie_file, context)
                browser.visit_page(target_url, context)
                return None
            context.push_message("warning", "EnsureAuth: User reported not logged in")
        else:
            context.push_message("warning", "EnsureAuth: Session invalid or expired, manual login required")

        if browser.is_headless():
            context.push_message("info", "EnsureAuth: Switching to visible browser for login")
            browser.switch_to_visible()

        browser.visit_page(target_url, context)

        if success_selector:
            context.push_message("info", f"EnsureAuth: Waiting for success selector: {success_selector}")
            self._wait_for_success(browser, success_selector, context)
        else:
            self._prompt_manual_login(context)

        self._save_cookies(browser, cookie_file, context)
        context.push_message("info", "EnsureAuth: Cookies saved successfully")

        stay_visible = step_config.get('stay_visible', False)

        if stay_visible:
            context.push_message("info", "EnsureAuth: Staying in visible mode (debug mode)")
        elif not browser.is_headless():
            context.push_message("info", "EnsureAuth: Switching back to headless mode")
            browser.switch_to_headless()
            context.push_message("info", "EnsureAuth: Reloading cookies into headless session")
            browser.visit_page(target_url, context)
            time.sleep(0.5)
            self._try_load_cookies(browser, cookie_file, context)

        context.push_message("info", "EnsureAuth: Authentication complete")
        return None

    def _extract_domain(self, url):
        parsed = urlparse(url)
        domain = parsed.netloc
        domain = domain.replace(":", "_port_")
        return domain

    def _get_cookies_dir(self):
        cookies_dir = os.path.join(os.getcwd(), "cookies")
        if not os.path.exists(cookies_dir):
            os.makedirs(cookies_dir)
        return cookies_dir

    def _try_load_cookies(self, browser, cookie_file, context):
        if not os.path.exists(cookie_file):
            context.push_message("info", "EnsureAuth: No saved cookies found")
            return False

        try:
            with open(cookie_file, "rb") as f:
                cookies = pickle.load(f)
            browser.driver.delete_all_cookies()
            for cookie in cookies:
                if 'sameSite' in cookie:
                    if cookie['sameSite'] == 'None':
                        cookie['sameSite'] = 'Strict'
                browser.driver.add_cookie(cookie)
            context.push_message("info", f"EnsureAuth: Loaded {len(cookies)} cookies from file")
            return True
        except Exception as e:
            context.push_message("warning", f"EnsureAuth: Failed to load cookies: {e}")
            return False

    def _save_cookies(self, browser, cookie_file, context):
        try:
            cookies_dir = self._get_cookies_dir()
            cookies = browser.driver.get_cookies()
            with open(cookie_file, "wb") as f:
                pickle.dump(cookies, f)
            context.push_message("info", f"EnsureAuth: Saved {len(cookies)} cookies to file")
        except Exception as e:
            context.push_message("error", f"EnsureAuth: Failed to save cookies: {e}")

    def _check_auth_valid(self, browser, success_selector, context):
        if not success_selector:
            return False

        try:
            elements = browser.driver.find_elements(By.CSS_SELECTOR, success_selector)
            if elements:
                context.push_message("info", "EnsureAuth: Success selector found, auth is valid")
                return True
            return False
        except Exception:
            return False

    def _wait_for_success(self, browser, success_selector, context):
        try:
            wait = WebDriverWait(browser.driver, 86400)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, success_selector)))
        except Exception:
            context.push_message("warning", "EnsureAuth: Success selector not found, auth may have failed")

    def _prompt_manual_login(self, context):
        def show_dialog():
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            result = messagebox.askyesno(
                "Manual Login Required",
                "Please log in manually in the browser window.\n\n"
                "When you are finished, click Yes to continue."
            )
            root.destroy()
            return result

        if not show_dialog():
            context.push_message("warning", "EnsureAuth: User cancelled manual login")

    def _ask_user_auth_status(self, context):
        def show_dialog():
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)
            result = messagebox.askyesno(
                "Verify Login Status",
                "No success selector configured.\n\n"
                "Are you already logged in to the site?\n"
                "(Click 'Yes' if you see your profile/avatar)"
            )
            root.destroy()
            return result

        return show_dialog()
