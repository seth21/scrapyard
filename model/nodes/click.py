import time
from model.nodes.base import BaseNode
from model.nodes.registry import register_node
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import hashlib

@register_node("click")
class ClickNode(BaseNode):

    def execute(self, step_config, context, browser, engine, context_soup=None, inherited_data=None):
        selector = step_config['selector']
        wait_strategy = step_config.get("wait_strategy", "none")
        wait_timeout = float(step_config.get("wait_timeout", 10))
        wait_selector = step_config.get("wait_selector", "")
        delay_after = float(step_config.get("delay_after", 0.5))
        optional = bool(step_config.get("optional", False))
        try:
            elements = WebDriverWait(browser.driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector))
            )
        except:
            if optional:
                context.push_message("warning", "Click skipped (optional, not found)")
                # break
            else:
                context.push_message("error", "Click is not optional and was not found!")
                raise

        """if self.index >= len(elements):
            if self.optional:
                ctx.push_message("info", "Click skipped (index out of range)")
                return
            raise RuntimeError("Click index out of range")

        el = elements[self.index]"""
        el = elements[0]

        WebDriverWait(browser.driver, 10).until(EC.element_to_be_clickable(el))

        context.push_message("info", f"Clicking element: {selector}")

        old_hash = self._dom_hash(browser.driver)
        old_url = browser.driver.current_url

        browser.driver.execute_script("arguments[0].scrollIntoView({block:'center'})", el)
        time.sleep(0.2)
        browser.driver.execute_script("arguments[0].click();", el)

        self._wait_for_change(browser.driver, wait_strategy, wait_timeout, wait_selector, old_hash, old_url, context)

        if delay_after:
            time.sleep(delay_after)
        html = browser.driver.page_source

        #engine.active_soup = BeautifulSoup(html, "html.parser")
        current_url = browser.driver.current_url
        context.push_message("info", f"New URL: {current_url}")

    def _dom_hash(self, driver):
        return hashlib.md5(
            driver.execute_script("return document.body.innerHTML")
            .encode("utf-8")
        ).hexdigest()

    def _wait_for_change(self, driver, strategy, timeout, selector, old_hash, old_url, ctx):
        if strategy == "none":
            return

        wait = WebDriverWait(driver, timeout)

        if strategy == "dom_change":
            wait.until(lambda d: self._dom_hash(d) != old_hash)

        elif strategy == "url_change":
            wait.until(lambda d: d.current_url != old_url)

        elif strategy == "element_appears":
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))

        elif strategy == "element_disappears":
            wait.until_not(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))

        else:
            raise ValueError(f"Unknown wait strategy: {strategy}")
