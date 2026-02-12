from urllib.parse import urljoin
from model.nodes.base import BaseNode
from model.nodes.registry import register_node
import time
from bs4 import BeautifulSoup

@register_node("repeat")
class RepeatNode(BaseNode):

    def execute(self, step_config, context, browser, engine, context_soup=None, inherited_data=None):
        selector = step_config['selector']
        condition = step_config.get("mode", "fixed")
        count_value = int(step_config.get("count_value", 0))
        max_iter = int(step_config.get("max_iter", 0))
        delay = step_config.get("delay", 1.0)
        sub_steps = step_config.get("children", [])
        #current_soup = engine.active_soup
        # Initialize the repeat node's stack item
        context.repeat_stack.append({
            "seen_items": set()
        })
        if condition in ['fixed', 'count_lt'] and max_iter <= 0:
            max_iter = 50
            context.push_message("info",
                             f"   > Repeat started with fixed/count_lt mode detected but invalid max iterations (should be > 0), forcing to 50)")
        else:
            context.push_message("info", f"   > Repeat started (max={max_iter})")

        iteration = 0
        # This will hold the rows from Iteration 1, Iteration 2, etc.
        all_repeat_rows = []

        while True:
            if context.is_stopped(): break

            if 0 < max_iter <= iteration:
                context.push_message("info", "Repeat reached max iterations")
                break

            if not self._wait_for_repeat_condition(condition, selector, count_value, browser):
                context.push_message("info", "Repeat condition no longer met")
                break

            context.push_message("info", f"   > Repeat iteration {iteration + 1}")
            iteration_results = engine.process_steps(sub_steps, context, browser, context_soup=None, inherited_data=inherited_data)

            # 4. AGGREGATION
            # If the children found data, add it to our master list.
            if iteration_results:
                all_repeat_rows.extend(iteration_results)
            iteration += 1
            time.sleep(delay)

        context.repeat_stack.pop()
        # 6. RETURN VALUE
        # We return a LIST.
        # The Engine's "elif isinstance(result, list):" block will catch this
        # and extend the main 'child_rows' list with these results.
        return all_repeat_rows

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