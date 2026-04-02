from model.nodes.base import BaseNode
from model.nodes.registry import register_node


@register_node("extract")
class ExtractNode(BaseNode):

    def execute(self, step_config, context, browser, engine, context_soup=None, inherited_data=None):
        if step_config.get('discard_duplicates'):
            if 'seen_hashes' not in step_config:
                step_config['seen_hashes'] = set()
            if 'seen_urls' not in step_config:
                step_config['seen_urls'] = set()

        name = step_config['name']
        multi = int(step_config['multi'])
        selector = step_config['selector']
        current_soup = context_soup
        text = ""
        if multi:
            separator = step_config['sep']
            targets = current_soup.select(selector)
            extracted_values = []

            for t in targets:
                if step_config.get('attr'):
                    val = t.get(step_config['attr'], "")
                    if val:
                        if self._is_duplicate(val, step_config, is_url=True):
                            continue
                        extracted_values.append(val)
                else:
                    if bool(step_config['formatting']):
                        val = t.get_text(separator="\n", strip=True)
                    else:
                        val = t.get_text(strip=True)
                    if val:
                        if self._is_duplicate(val, step_config, is_url=False):
                            continue
                        extracted_values.append(val)
            text = separator.join(extracted_values)
        else:
            target = current_soup.select_one(selector) if selector else current_soup
            if target:
                if step_config.get('attr'):
                    text = target.get(step_config['attr'], "")
                    if text and self._is_duplicate(text, step_config, is_url=True):
                        context.push_message("info", f"   > {name}: [duplicate skipped]")
                        return {name: ""}
                else:
                    if bool(step_config['formatting']):
                        text = target.get_text(separator="\n", strip=True)
                    else:
                        text = target.get_text(strip=True)
                    if text and self._is_duplicate(text, step_config, is_url=False):
                        context.push_message("info", f"   > {name}: [duplicate skipped]")
                        return {name: ""}

        context.push_message("info", f"   > Extracted {name}: {text[:30]}...")
        return {name: text}

    def _is_duplicate(self, value, step_config, is_url=False):
        if not step_config.get('discard_duplicates'):
            return False

        tracker = step_config['seen_hashes'] if not is_url else step_config['seen_urls']
        h = hash(value.strip())
        if h in tracker:
            return True
        tracker.add(h)
        return False