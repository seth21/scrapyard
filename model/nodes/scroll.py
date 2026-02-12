import itertools
from model.nodes.base import BaseNode
from model.nodes.registry import register_node
import time
from bs4 import BeautifulSoup

@register_node("scroll")
class ScrollNode(BaseNode):

    def execute(self, step_config, context, browser, engine, context_soup=None, inherited_data=None):
        self._handle_scroll(step_config, browser, context)

    def _handle_scroll(self, step, browser, ctx):
        driver = browser.driver

        mode = step.get("mode", "bottom")
        times = step.get("times", 1)
        delay = step.get("delay", 0.2)
        wait_cfg = step.get("wait", {})
        wait_strategy = wait_cfg.get("strategy", "height_change")
        wait_timeout = wait_cfg.get("timeout", 5)

        ctx.push_message("info", f"Scrolling ({mode}) x{times}")

        for i in range(times):
            old_height = driver.execute_script(
                "return document.body.scrollHeight"
            )
            old_html = driver.page_source

            # --- Perform scroll ---
            if mode == "bottom":
                driver.execute_script(
                    "window.scrollTo(0, document.body.scrollHeight)"
                )

            elif mode == "top":
                driver.execute_script(
                    "window.scrollTo(0, 0)"
                )

            elif mode == "by":
                distance = step.get("distance", 500)
                driver.execute_script(
                    "window.scrollBy(0, arguments[0])", distance
                )

            elif mode == "to":
                selector = step.get("selector")
                if not selector:
                    ctx.push_message("error", "Scroll 'to' requires selector")
                    break

                el = driver.find_element("css selector", selector)
                driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'})", el
                )

            # --- Wait for page to update ---
            self._wait_after_scroll(
                driver,
                wait_strategy,
                wait_timeout,
                old_height,
                old_html
            )

            time.sleep(delay)

        #return BeautifulSoup(driver.page_source, "html.parser")

    def _wait_after_scroll(
            self,
            driver,
            strategy,
            timeout,
            old_height,
            old_html
    ):
        end_time = time.time() + timeout

        while time.time() < end_time:
            if strategy == "height_change":
                new_height = driver.execute_script(
                    "return document.body.scrollHeight"
                )
                if new_height > old_height:
                    return

            elif strategy == "dom_change":
                if driver.page_source != old_html:
                    return

            elif strategy == "none":
                return

            time.sleep(0.2)