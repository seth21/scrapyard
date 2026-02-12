from urllib.parse import urljoin
from model.nodes.base import BaseNode
from model.nodes.registry import register_node
import time
from bs4 import BeautifulSoup

@register_node("visit")
class VisitNode(BaseNode):

    def execute(self, step_config, context, browser, engine, context_soup=None, inherited_data=None):
        selector = step_config['selector']
        # VISIT implies we find a link, go there, run SUB-STEPS, then come back
        sub_steps = step_config['children']
        original_url = browser.driver.current_url
        original_soup = context_soup
        # Did our parent tell us we can skip cleanup?
        can_skip_restore = inherited_data.get('_skip_restore', False) if inherited_data else False
        visited_rows = []

        new_url = None
        #If the passed soup is a string, just use that as URL
        if isinstance(original_soup, str):
            new_url = original_soup
        else:
            # LOGIC UPDATE: If selector is empty, use the current loop element as the link
            if not selector:
                link_el = original_soup
            else:
                link_el = original_soup.select_one(selector)
            if link_el and link_el.name == 'a' and link_el.get('href'):
                new_url = urljoin(original_url, link_el.get('href'))
                context.push_message("info", f"   > Visiting: {new_url}")
                time.sleep(1)  # Polite delay
        if not new_url: return []

        try:
            html = browser.visit_page(new_url, context)
            # RECURSION: Process children on new page
            visited_rows = engine.process_steps(sub_steps, context, browser, context_soup=None, inherited_data=inherited_data)
        except Exception as e:
            context.push_message("error", f"     Error visiting link: {e}")
        if can_skip_restore is False:
            # Returns to original page after visit is done
            browser.visit_page(original_url, context)
            #engine.active_soup = original_soup
            context.push_message("info", f"Returned to {original_url}")
        # We return the list of rows found on that sub-page.
        # The Engine will catch this list and add it to the results.
        return visited_rows