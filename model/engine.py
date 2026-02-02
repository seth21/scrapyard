import itertools

from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import hashlib
from model.browser import SeleniumDriver
from urllib.parse import urljoin
import time

from model.context import Context


# --- DATA STRUCTURES ---
# We use a simple list of dictionaries to represent the "Workflow Plan"
# Example: [{'type': 'extract', 'selector': 'h1', 'name': 'Title'}, ...]

class ScraperEngine:
    """
    The brain that executes the workflow plan.
    """

    def __init__(self):
        self.results = []  # Final data list
        self.stop_flag = False

    def run(self, steps, base_url, browser: SeleniumDriver, ctx:Context):
        self.results = []
        self.stop_flag = False
        current_url = base_url
        page_num = 1
        ctx.push_message("info", f"--- Starting Job on {current_url} ---")

        try:
            ctx.push_message("info", f"--- Processing Page {page_num} ---")
            html = browser.visit_page(current_url, ctx)
            soup = BeautifulSoup(html, 'html.parser')
            #print(steps)
            # Start the recursive processing
            # We treat the initial page as a single item context
            self._process_steps(steps, soup, {}, current_url, browser, ctx)

        except Exception as e:
            ctx.push_message("error", f"Critical Engine Error: {e}")
        finally:
            ctx.push_message("info", f"--- Job Complete. Extracted {len(self.results)} rows. ---")
        return self.results


    def _process_steps(self, steps, current_soup, current_data_row, current_url, browser: SeleniumDriver, ctx:Context):
        """
        Recursive function to handle nested loops and visits.
        steps: list of step dicts to execute
        current_soup: the BS4 object we are currently looking at
        current_data_row: the dictionary we are building (e.g., {'Title': 'X'})
        """
        if self.stop_flag: return

        # Copy row so we don't overwrite data from previous loop iterations
        row_snapshot = current_data_row.copy()

        for i, step in enumerate(steps):
            if self.stop_flag: break

            s_type = step['type']
            selector = step['selector']

            if s_type == 'extract':
                name = step['name']
                multi = int(step['multi'])
                text = ""
                if multi:
                    separator = step['sep']
                    # Find ALL matches
                    targets = current_soup.select(selector)
                    extracted_values = []

                    for t in targets:
                        if step.get('attr'):
                            val = t.get(step['attr'], "")
                        else:
                            if bool(step['formatting']):
                                val = t.get_text(separator="\n", strip=True)
                            else:
                                val = t.get_text(strip=True)
                        if val: extracted_values.append(val)
                    # JOIN THEM (e.g., with a comma)
                    text = separator.join(extracted_values)
                # If selector is empty, use current context
                else:
                    target = current_soup.select_one(selector) if selector else current_soup
                    if target:
                        if step.get('attr'):  # Extract attribute like 'href' or 'src'
                            text = target.get(step['attr'], "")
                        else:
                            if bool(step['formatting']):
                                text = target.get_text(separator="\n", strip=True)
                            else:
                                text = target.get_text(strip=True)

                row_snapshot[name] = text
                ctx.push_message("info", f"   > Extracted {name}: {text[:30]}...")

            elif s_type == 'loop':
                # LOOP implies we find multiple items and run SUB-STEPS on them
                sub_steps = step['children']
                elements = current_soup.select(selector)
                limit = int(step['limit'])
                if limit and limit > 0:
                    ctx.push_message("info", f"   > Loop found {min(len(elements), limit)} items. Processing...")
                    for el in itertools.islice(elements, 0, limit):
                        self._process_steps(sub_steps, el, row_snapshot, current_url, browser, ctx)
                else:
                    ctx.push_message("info", f"   > Loop found {len(elements)} items. Processing...")
                    for el in elements:
                        # RECURSION: Process children with the element as the new 'soup'
                        current_soup = self._process_steps(sub_steps, el, row_snapshot, current_url, browser, ctx)

                # If we entered a loop, the linear flow for this 'row_snapshot' ends here
                # because the loop handles the saving of the multiple resulting rows.
                #return current_soup

            elif s_type == 'visit':
                # VISIT implies we find a link, go there, run SUB-STEPS, then come back
                sub_steps = step['children']
                original_url = browser.driver.current_url
                # LOGIC UPDATE: If selector is empty, use the current loop element as the link
                if not selector:
                    link_el = current_soup
                else:
                    link_el = current_soup.select_one(selector)

                if link_el and link_el.name == 'a' and link_el.get('href'):
                    new_url = urljoin(current_url, link_el.get('href'))
                    ctx.push_message("info", f"   > Visiting: {new_url}")
                    time.sleep(1)  # Polite delay

                    try:
                        html = browser.visit_page(new_url, ctx)
                        sub_soup = BeautifulSoup(html, 'html.parser')
                        # RECURSION: Process children on new page
                        self._process_steps(sub_steps, sub_soup, row_snapshot, new_url, browser, ctx)
                    except Exception as e:
                        ctx.push_message("error", f"     Error visiting link: {e}")
                    # Returns to original page after visit is done
                    browser.visit_page(original_url, ctx)
                    ctx.push_message("info", f"Returned to {original_url}")
                #return current_soup

            elif s_type == "repeat":
                condition = step.get("mode", "fixed")
                count_value = int(step.get("count_value", 0))
                max_iter = int(step.get("max_iter", 0))
                delay = step.get("delay", 1.0)
                sub_steps = step.get("children", [])
                #Initialize the repeat node's stack item
                ctx.repeat_stack.append({
                    "seen_items": set()
                })
                if condition in ['fixed', 'count_lt']:
                    max_iter = 50
                    ctx.push_message("info", f"   > Repeat started with fixed/count_lt mode detected but invalid max iterations (should be > 0), forcing to 50)")
                else:
                    ctx.push_message("info", f"   > Repeat started (max={max_iter})")

                iteration = 0
                repeat_base_soup = current_soup
                while True:
                    if self.stop_flag: break

                    if 0 < max_iter <= iteration:
                        ctx.push_message("info", "Repeat reached max iterations")
                        break

                    if not self._wait_for_repeat_condition(condition, selector, count_value, browser):
                        ctx.push_message("info", "Repeat condition no longer met")
                        break

                    ctx.push_message("info", f"   > Repeat iteration {iteration + 1}")

                    repeat_base_soup = self._process_steps(
                        sub_steps,
                        repeat_base_soup,
                        row_snapshot,
                        current_url,
                        browser,
                        ctx
                    )

                    iteration += 1
                    time.sleep(delay)
                ctx.repeat_stack.pop()
                #return current_soup
                current_soup = repeat_base_soup

            elif s_type == "click":
                wait_strategy = step.get("wait_strategy", "none")
                wait_timeout = float(step.get("wait_timeout", 10))
                wait_selector = step.get("wait_selector", "")
                delay_after = float(step.get("delay_after", 0.5))
                optional = bool(step.get("optional", False))
                try:
                    elements = WebDriverWait(browser.driver, 10).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector))
                    )
                except:
                    if optional:
                        ctx.push_message("warning", "Click skipped (optional, not found)")
                        #break
                    else:
                        ctx.push_message("error", "Click is not optional and was not found!")
                        raise

                """if self.index >= len(elements):
                    if self.optional:
                        ctx.push_message("info", "Click skipped (index out of range)")
                        return
                    raise RuntimeError("Click index out of range")

                el = elements[self.index]"""
                el = elements[0]

                WebDriverWait(browser.driver, 10).until(EC.element_to_be_clickable(el))

                ctx.push_message("info", f"Clicking element: {selector}")

                old_hash = self._dom_hash(browser.driver)
                old_url = browser.driver.current_url

                browser.driver.execute_script("arguments[0].scrollIntoView({block:'center'})", el)
                time.sleep(0.2)
                browser.driver.execute_script("arguments[0].click();", el)

                self._wait_for_change(browser.driver, wait_strategy, wait_timeout, wait_selector, old_hash, old_url, ctx)

                if delay_after:
                    time.sleep(delay_after)
                html = browser.driver.page_source

                current_soup = BeautifulSoup(html, "html.parser")
                current_url = browser.driver.current_url
                ctx.push_message("info", f"New URL: {current_url}")

            elif s_type == "scroll":
                current_soup = self._handle_scroll(step, browser, ctx)
                #return current_soup
                #continue

        # End of steps: If we have data and we are not inside a parent structure that is still building
        # We save the row.
        if row_snapshot:
            self.results.append(row_snapshot)
        return current_soup

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

        return BeautifulSoup(driver.page_source, "html.parser")

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


    def _wait_for_repeat_condition(
            self,
            ctype,
            selector,
            value,
            browser,
            timeout=5,
            poll=0.2
    ):
        end_time = time.time() + timeout

        while time.time() < end_time:
            soup = BeautifulSoup(browser.driver.page_source, "html.parser")

            if self._evaluate_condition(ctype, selector, value, soup):
                return True

            time.sleep(poll)

        return False

    def _evaluate_condition(self, ctype, selector, value, soup):
        if ctype == "exists":
            return soup.select_one(selector) is not None

        if ctype == "not_exists":
            return soup.select_one(selector) is None

        if ctype == "count_lt":
            return len(soup.select(selector)) < value

        if ctype == "fixed":
            return True

        return False