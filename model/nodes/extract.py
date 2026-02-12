from model.nodes.base import BaseNode
from model.nodes.registry import register_node

@register_node("extract")
class ExtractNode(BaseNode):

    def execute(self, step_config, context, browser, engine, context_soup=None, inherited_data=None):
        name = step_config['name']
        multi = int(step_config['multi'])
        selector = step_config['selector']
        current_soup = context_soup
        text = ""
        if multi:
            separator = step_config['sep']
            # Find ALL matches
            targets = current_soup.select(selector)
            extracted_values = []

            for t in targets:
                if step_config.get('attr'):
                    val = t.get(step_config['attr'], "")
                else:
                    if bool(step_config['formatting']):
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
                if step_config.get('attr'):  # Extract attribute like 'href' or 'src'
                    text = target.get(step_config['attr'], "")
                else:
                    if bool(step_config['formatting']):
                        text = target.get_text(separator="\n", strip=True)
                    else:
                        text = target.get_text(strip=True)

        context.push_message("info", f"   > Extracted {name}: {text[:30]}...")
        # Return data to be merged into the row
        return {name: text}