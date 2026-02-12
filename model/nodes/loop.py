from bs4 import BeautifulSoup
from model.nodes.base import BaseNode
from model.nodes.registry import register_node

@register_node("loop")
class LoopNode(BaseNode):

    def execute(self, step_config, context, browser, engine, context_soup=None, inherited_data=None):
        selector = step_config['selector']
        # LOOP implies we find multiple items and run SUB-STEPS on them
        sub_steps = step_config['children']
        elements = context_soup.select(selector)
        limit = int(step_config.get('limit', 0))

        # ANALYZE ITEMS (Smart Detection)
        # We always keep the full Element (Tag).
        # BS4 Tags are safe to hold in memory even if the page changes.
        items_to_process = context_soup.select(selector)

        # We capture the 'Home Base' URL so we can return if needed.
        main_page_url = browser.driver.current_url

        all_loop_rows = []
        context.push_message("info", f"   > Loop found {min(len(elements), limit) if limit > 0 else len(elements)} items. Processing...")
        for i, item in enumerate(items_to_process):
            if i >= limit > 0:
                break
            # We check if this item IS a link, but we don't convert it.
            # We just note it down to tell the children what to do.
            is_link = False
            if item.name == 'a' and item.has_attr('href'):
                is_link = True
            elif item.select_one('a[href]'):
                is_link = True
            # If it is a link, we tell the VisitNode: "You don't need to go back."
            child_data = inherited_data.copy() if inherited_data else {}
            if is_link:
                child_data['_skip_restore'] = True
            # If we are looping over DOM Elements (not strings), we MUST be on the list page.
            # If the previous iteration moved us (e.g. clicked something), we must go back.
            if not is_link:
                if browser.driver.current_url != main_page_url:
                    context.push_message("info", "Loop: Restoring state to main page...")
                    browser.visit_page(main_page_url, context)

                    # CRITICAL: Refresh the soup and re-find the element!
                    # The old 'item' variable is dead (StaleElement).
                    html = browser.driver.page_source
                    new_soup = BeautifulSoup(html, 'html.parser')
                    current_items = new_soup.select(selector)

                    if i < len(current_items):
                        item = current_items[i]  # Update 'item' to the live element
                    else:
                        context.push_message("warning", "Loop: Item missing after refresh. Skipping.")
                        continue
            try:
                # We pass the 'child_data' which contains our secret flag
                item_rows = engine.process_steps(sub_steps, context, browser, context_soup=item, inherited_data=child_data)
                all_loop_rows.extend(item_rows)

            except Exception as e:
                context.push_message("error", f"Loop Error on item {i}: {e}")

        # If we are in Optimized Mode, we likely drifted far away (Page 50).
        # We should return to the list page so any subsequent steps (like Pagination) work.
        if browser.driver.current_url != main_page_url:
            browser.visit_page(main_page_url, context)

        return all_loop_rows