import tkinter as tk
from tkinter import ttk, filedialog
import customtkinter as ct
from typing import Callable
import json

ct.set_appearance_mode("system")
ct.set_default_color_theme("blue")

class View(ct.CTk):
    def __init__(self):
        super().__init__()
        self.title("Scrapyard v1.0")
        self.geometry("1000x700")
        self.resizable(width=False, height=False)
        self.configure(bg="white")
        self.grid_columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.root_steps = []  # List of StepBlock widgets
        self.step_map = {}  # Maps Tree Item ID -> Step Data Dictionary
        self.current_selection_id = None
        self.create_config_frame()
        self.create_preview_frame()
        self.create_workflow_builder()

        self.log_message("System ready. Waiting for configuration...")

    def create_config_frame(self):
        #Left sidebar (config) and buttons at bottom
        self.config_frame = ct.CTkFrame(self, corner_radius=0)
        self.config_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.columnconfigure(0, weight=0)

        self.logo_label = ct.CTkLabel(self.config_frame, text="Crawler Config", font=ct.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=10)

        # 1. Base URL
        self.url_label = ct.CTkLabel(self.config_frame, text="Starting URL:")
        self.url_label.grid(row=1, column=0, padx=20, pady=5, sticky="w")
        self.url_entry = ct.CTkEntry(self.config_frame, placeholder_text="https://imdb.com/chart/top")
        self.url_entry.grid(row=2, column=0, padx=20, pady=(0, 10), sticky="ew")

        # Toolbox
        self.add_action_label = ct.CTkLabel(self.config_frame, text="Add Action", font=("Arial", 16, "bold"))
        self.add_action_label.grid(row=3, column=0, padx=20, pady=(0, 10), sticky="ew")
        self.extract_data_button = ct.CTkButton(self.config_frame, text="+ Extract (Single)", command=lambda: self.add_node("extract"))
        self.extract_data_button.grid(row=4, column=0, padx=20, pady=(0, 10), sticky="ew")
        self.loop_button = ct.CTkButton(self.config_frame, text="+ Loop (For Each)", fg_color="#d97b26",
                                command=lambda: self.add_node("loop"))
        self.loop_button.grid(row=5, column=0, padx=20, pady=(0, 10), sticky="ew")
        self.repeat_button = ct.CTkButton(self.config_frame, text="+ Repeat", fg_color="#a0522d",
                                        command=lambda: self.add_node("repeat"))
        self.repeat_button.grid(row=6, column=0, padx=20, pady=(0, 10), sticky="ew")
        self.visit_link_button = ct.CTkButton(self.config_frame, text="+ Visit Link", fg_color="#2a8a58",
                                command=lambda: self.add_node("visit"))
        self.visit_link_button.grid(row=7, column=0, padx=20, pady=(0, 10), sticky="ew")
        self.visit_click_button = ct.CTkButton(self.config_frame, text="+ Click Button", fg_color="#006400",
                                              command=lambda: self.add_node("click"))
        self.visit_click_button.grid(row=8, column=0, padx=20, pady=(0, 10), sticky="ew")
        self.ensure_auth_button = ct.CTkButton(self.config_frame, text="+ Ensure Auth", fg_color="#8b4513",
                                               command=lambda: self.add_node("ensure_auth"))
        self.ensure_auth_button.grid(row=8, column=0, padx=20, pady=(0, 10), sticky="ew")
        self.scroll_button = ct.CTkButton(self.config_frame, text="+ Scroll Button", fg_color="#45818e",
                                               command=lambda: self.add_node("scroll"))
        self.scroll_button.grid(row=9, column=0, padx=20, pady=(0, 10), sticky="ew")
        self.delete_step_button = ct.CTkButton(self.config_frame, text="Delete Selected Step", fg_color="#c42b1c",
                                command=self.delete_node)
        self.delete_step_button.grid(row=10, column=0, padx=20, pady=(0, 10), sticky="ew")
        self.instructions_label = ct.CTkLabel(self.config_frame, text="Instructions:", font=("Arial", 12, "bold"))
        self.instructions_label.grid(row=11, column=0, padx=20, pady=(0, 10), sticky="ew")
        help_txt = ("1. Select the container (Loop/Visit)\n   to add inside it.\n"
                    "2. If nothing selected, adds to root.\n"
                    "3. 'Selector' is CSS (e.g. .title)")
        self.instructions_details = ct.CTkLabel(self.config_frame, text=help_txt, justify="left", text_color="gray")
        self.instructions_details.grid(row=12, column=0, padx=20, pady=(0, 10), sticky="ew")

        # Buttons
        self.scrape_button = ct.CTkButton(self.config_frame, text="Run Scraper")
        self.scrape_button_default_color = self.scrape_button.cget("fg_color")
        self.scrape_button.grid(row=13, column=0, padx=20, pady=10)

        self.export_button = ct.CTkButton(self.config_frame, text="Export to Excel", fg_color="green", state="disabled")
        self.export_button.grid(row=14, column=0, padx=20, pady=10)

        self.selected_parent = None

    def create_workflow_builder(self):
        # 2. LEFT: TREEVIEW (The Structure)
        # CustomTkinter doesn't have a Tree, so we use standard TTK with dark styling
        self.tree_frame = ct.CTkFrame(self)
        self.tree_frame.grid(row=1, column=1, sticky="nsew", padx=10, pady=5)

        # Style the Treeview to match Dark Mode
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="#2b2b2b", fieldbackground="#2b2b2b", foreground="white", rowheight=25)
        style.map('Treeview', background=[('selected', '#1f538d')])

        self.tree = ttk.Treeview(self.tree_frame, selectmode="browse")
        self.tree.pack(fill="both", expand=True, padx=5, pady=5)
        self.tree.heading("#0", text="Workflow Steps (Structure)", anchor="w")
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)

        # Initialize Root
        self.root_id = self.tree.insert("", "end", text="START", open=True)
        self.step_map[self.root_id] = {"type": "root", "children": []}

        # Properties Area (Dynamic)
        self.props_container = ct.CTkFrame(self, fg_color="transparent")
        self.props_container.grid(row=1, column=2, sticky="nsew", padx=10, pady=5)
        ct.CTkLabel(self.props_container, text="Step Properties", font=("Arial", 14, "bold")).pack(
            pady=(20, 10))


    def on_tree_select(self, event):
        self.clear_inspector()
        selected = self.tree.selection()
        if not selected: return

        item_id = selected[0]
        if item_id == self.root_id: return  # Root has no props

        self.current_selection_id = item_id
        data = self.step_map[item_id]

        # Draw inputs based on type
        self.create_prop_entry("CSS Selector:", "selector", data)

        if data['type'] == 'extract':
            self.create_prop_entry("Column Name:", "name", data)
            self.create_prop_entry("Attribute (opt):", "attr", data)
            self.create_prop_checkbox("Multi-Mode:", "multi", data)
            self.create_prop_entry("Multi-Separator (opt):", "sep", data)
            self.create_prop_checkbox("Preserve formatting:", "formatting", data)
            self.create_prop_checkbox("Discard Duplicates:", "discard_duplicates", data)
        if data['type'] == 'loop':
            self.create_prop_entry("Limit:", "limit", data)
        if data['type'] == 'repeat':
            def disable_value_entry(choice, target_widget):
                if choice == "count_lt":
                    target_widget.configure(state="normal")
                else:
                    target_widget.configure(state="disabled")
            self.create_prop_entry("Max iterations:", "max_iter", data)
            value_widget = self.create_prop_entry("Count condition value:", "count_value", data)

            self.create_prop_dropdown("Type:", "mode", data, values=["fixed", "exists", "not_exists", "count_lt"], change_callback=lambda choice: disable_value_entry(choice, value_widget))
        if data['type'] == 'click':
            self.create_prop_dropdown("Wait strategy:", "wait_strategy", data, values=["none", "dom_change", "element_appears", "element_disappears", "url_change"],
                                      change_callback=None)
            self.create_prop_entry("Wait selector (opt):", "wait_selector", data)
            self.create_prop_entry("Wait timeout:", "wait_timeout", data)
            self.create_prop_entry("Delay after click:", "delay_after", data)
            self.create_prop_checkbox("Optional:", "optional", data)
        if data['type'] == 'scroll':
            self.create_prop_dropdown("Mode:", "mode", data, values=["bottom", "top", "selector"], change_callback=None)
            self.create_prop_dropdown("Wait strategy:", "wait_strategy", data, values=["dom_change", "height_change", "none"],
                                      change_callback=None)
            self.create_prop_entry("Wait timeout:", "wait_timeout", data)
        if data['type'] == 'ensure_auth':
            self.create_prop_entry("Login URL (optional):", "login_url", data)
            self.create_prop_entry("Success Selector (optional):", "success_selector", data)
            self.create_prop_entry("Cookie Name (optional):", "cookie_name", data)
            self.create_prop_checkbox("Stay Visible:", "stay_visible", data)

    def create_prop_entry(self, label_text, key, data_dict):
        """Helper to create a label + entry that auto-updates the dictionary"""
        lbl = ct.CTkLabel(self.props_container, text=label_text, anchor="w")
        lbl.pack(fill="x", pady=(5, 0))

        entry = ct.CTkEntry(self.props_container)
        entry.insert(0, data_dict.get(key, ""))
        entry.pack(fill="x", pady=(0, 5))

        # Auto-save on key release
        def save_val(e):
            data_dict[key] = entry.get()
            # Update tree text if name changes
            if key == 'name':
                self.tree.item(self.current_selection_id, text=f"📄 {entry.get()}")

        entry.bind("<KeyRelease>", save_val)
        return entry

    def create_prop_checkbox(self, label_text, key, data_dict):
        def checkbox_event():
            data_dict[key] = checkbox.get()

        value = data_dict.get(key, 0)
        checkbox = ct.CTkCheckBox(self.props_container, text=label_text, command=checkbox_event)
        if value:
            checkbox.select()
        #checkbox..insert(0, data_dict.get(key, ""))
        checkbox.pack(fill="x", pady=(5, 5))

    def create_prop_dropdown(self, label_text, key, data_dict, values, change_callback=None):
        def combobox_event(choice):
            data_dict[key] = choice
            if change_callback:
                change_callback(choice)

        value = data_dict.get(key, values[0])
        checkbox = ct.CTkComboBox(self.props_container, values=values, command=combobox_event)
        if value:
            checkbox.set(value)
            if change_callback: change_callback(value)
        checkbox.pack(fill="x", pady=(5, 5))

    def clear_inspector(self):
        for widget in self.props_container.winfo_children():
            widget.destroy()
        self.current_selection_id = None

    def add_node(self, step_type):
        # Determine parent: Selected node or Root
        selected = self.tree.selection()
        if selected:
            parent_id = selected[0]
            # Can only add children to Root, Loop, or Visit
            p_data = self.step_map[parent_id]
            if p_data['type'] in ['extract', 'click', 'scroll', 'ensure_auth']:
                # If Extract, Scroll or Click selected, add to its parent instead
                parent_id = self.tree.parent(parent_id)
        else:
            parent_id = self.root_id

        # Insert Item
        text_map = {"extract": "📄 Extract Data", "loop": " ↩️ For Each Element", "visit": "🔗 Visit Link", "repeat": "🔁 Repeat", "click": "👇 Click", "scroll": "⚙ Scroll", "ensure_auth": "🔐 Ensure Auth"}
        new_id = self.tree.insert(parent_id, "end", text=text_map[step_type], open=True)

        # Default Data
        data = {"type": step_type, "selector": "", "name": "Column 1", "attr": "", "children": []}
        self.step_map[new_id] = data

        # Select the new item to edit immediately
        self.tree.selection_set(new_id)

    def delete_node(self):
        selected = self.tree.selection()
        if not selected or selected[0] == self.root_id: return
        item_id = selected[0]
        self.tree.delete(item_id)
        del self.step_map[item_id]
        self.clear_inspector()

    def create_preview_frame(self):
        # --- RIGHT SIDE (Preview / Console) ---
        self.right_frame = ct.CTkFrame(self)
        self.right_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew", columnspan=2)
        self.columnconfigure(1, weight=1)
        self.right_frame.grid_columnconfigure(0, weight=1)

        self.console_label = ct.CTkLabel(self.right_frame, text="Scraper Log & Output", font=ct.CTkFont(size=15, weight="bold"))
        self.console_label.grid(row=0, column=0, padx=20, pady=10, sticky="w")
        self.console_label.configure(state="disabled")

        # Textbox for logs
        self.console = ct.CTkTextbox(self.right_frame)
        self.console.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        self.console.tag_config("info", foreground="white")
        self.console.tag_config("error", foreground="red")
        self.console.tag_config("warning", foreground="orange")
        self.console.tag_config("done", foreground="green")

        # Progress Bar
        self.progress_bar = ct.CTkProgressBar(self.right_frame)
        self.progress_bar.grid(row=2, column=0, padx=20, pady=10, sticky="ew")
        self.progress_bar.set(0)

        # Import/Export Workflow Buttons
        self.button_frame = ct.CTkFrame(self.right_frame, fg_color="transparent")
        self.button_frame.grid(row=3, column=0, padx=20, pady=(0, 10), sticky="ew")
        self.button_frame.grid_columnconfigure(0, weight=1)
        self.button_frame.grid_columnconfigure(1, weight=1)

        self.import_wf_button = ct.CTkButton(self.button_frame, text="Import Workflow", fg_color="#456c9c",
                                          command=self.import_workflow)
        self.import_wf_button.grid(row=0, column=0, padx=(0, 5), sticky="ew")

        self.export_wf_button = ct.CTkButton(self.button_frame, text="Export Workflow", fg_color="#456c9c",
                                          command=self.export_workflow)
        self.export_wf_button.grid(row=0, column=1, padx=(5, 0), sticky="ew")

    def build_config_recursive(self, parent_id):
        """Walks the tree to build the JSON config for the engine"""
        steps = []
        for child_id in self.tree.get_children(parent_id):
            data = self.step_map[child_id]
            step_config = {
                "type": data['type'],
                "selector": data['selector'],
                "name": data.get('name', ''),
                "attr": data.get('attr', '')
            }
            if data['type'] in ['loop', 'visit', 'repeat']:
                step_config['children'] = self.build_config_recursive(child_id)
            if data['type'] in ['loop']:
                step_config['limit'] = data.get('limit', 0)
            if data['type'] == 'extract':
                step_config['sep'] = data.get('sep', ',')
                step_config['multi'] = data.get('multi', 0)
                step_config['formatting'] = data.get('formatting', 0)
                step_config['discard_duplicates'] = data.get('discard_duplicates', 0)
            if data['type'] == 'repeat':
                step_config['mode'] = data.get('mode', 'fixed')
                step_config['max_iter'] = data.get('max_iter', 0)
                step_config['count_value'] = data.get('count_value', 0)
            if data['type'] == 'click':
                step_config['wait_strategy'] = data.get('wait_strategy', 'none')
                step_config['wait_selector'] = data.get('wait_selector', '')
                step_config['wait_timeout'] = data.get('wait_timeout', 10)
                step_config['delay_after'] = data.get('delay_after', 0.5)
                step_config['optional'] = data.get('optional', False)
            if data['type'] == 'scroll':
                step_config['wait_strategy'] = data.get('wait_strategy', 'dom_change')
                step_config['wait_timeout'] = data.get('wait_timeout', 5)
                step_config['mode'] = data.get('mode', 'bottom')
            if data['type'] == 'ensure_auth':
                step_config['login_url'] = data.get('login_url', '')
                step_config['success_selector'] = data.get('success_selector', '')
                step_config['cookie_name'] = data.get('cookie_name', '')
                step_config['stay_visible'] = data.get('stay_visible', False)
            steps.append(step_config)
        return steps

    def log_message(self, message):
        """Helper to print text to the GUI console"""
        self.console.configure(state="normal")
        self.console.insert("end", message + "\n")
        self.console.see("end")  # Auto-scroll to bottom
        self.console.configure(state="disabled")

    def log_type_message(self, msgtype, message):
        """Helper to print text to the GUI console"""
        self.console.configure(state="normal")
        self.console.insert("end", str.upper(msgtype)+": "+message + "\n", msgtype)
        self.console.see("end")  # Auto-scroll to bottom
        self.console.configure(state="disabled")

    def import_workflow(self):
        file_path = filedialog.askopenfilename(
            title="Import Workflow",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if not file_path:
            return

        try:
            with open(file_path, 'r') as f:
                data = json.load(f)

            url = data.get('url', '')
            steps = data.get('steps', [])

            self.url_entry.delete(0, "end")
            self.url_entry.insert(0, url)

            for child_id in self.tree.get_children(self.root_id):
                self.tree.delete(child_id)
                del self.step_map[child_id]

            for step in steps:
                self._add_step_from_json(self.root_id, step)

            self.log_message(f"Workflow imported from {file_path}")

        except Exception as e:
            self.log_message(f"Error importing workflow: {e}")

    def _add_step_from_json(self, parent_id, step_data):
        step_type = step_data.get('type')
        text_map = {
            "extract": "📄 Extract Data", "loop": " ↩️ For Each Element",
            "visit": "🔗 Visit Link", "repeat": "🔁 Repeat",
            "click": "👇 Click", "scroll": "⚙ Scroll", "ensure_auth": "🔐 Ensure Auth"
        }
        display_text = text_map.get(step_type, f"📄 {step_type}")

        new_id = self.tree.insert(parent_id, "end", text=display_text, open=True)

        data = {
            "type": step_type,
            "selector": step_data.get('selector', ''),
            "name": step_data.get('name', 'Column 1'),
            "attr": step_data.get('attr', ''),
            "children": []
        }

        if step_type in ['loop', 'visit', 'repeat']:
            for child_step in step_data.get('children', []):
                self._add_step_from_json(new_id, child_step)
            data['children'] = step_data.get('children', [])

        if step_type == 'loop':
            data['limit'] = step_data.get('limit', 0)

        if step_type == 'extract':
            data['sep'] = step_data.get('sep', ',')
            data['multi'] = step_data.get('multi', 0)
            data['formatting'] = step_data.get('formatting', 0)
            data['discard_duplicates'] = step_data.get('discard_duplicates', 0)

        if step_type == 'repeat':
            data['mode'] = step_data.get('mode', 'fixed')
            data['max_iter'] = step_data.get('max_iter', 0)
            data['count_value'] = step_data.get('count_value', 0)

        if step_type == 'click':
            data['wait_strategy'] = step_data.get('wait_strategy', 'none')
            data['wait_selector'] = step_data.get('wait_selector', '')
            data['wait_timeout'] = step_data.get('wait_timeout', 10)
            data['delay_after'] = step_data.get('delay_after', 0.5)
            data['optional'] = step_data.get('optional', False)

        if step_type == 'scroll':
            data['wait_strategy'] = step_data.get('wait_strategy', 'dom_change')
            data['wait_timeout'] = step_data.get('wait_timeout', 5)
            data['mode'] = step_data.get('mode', 'bottom')

        if step_type == 'ensure_auth':
            data['login_url'] = step_data.get('login_url', '')
            data['success_selector'] = step_data.get('success_selector', '')
            data['cookie_name'] = step_data.get('cookie_name', '')
            data['stay_visible'] = step_data.get('stay_visible', False)

        self.step_map[new_id] = data

    def export_workflow(self):
        url = self.url_entry.get()
        steps = self.build_config_recursive(self.root_id)

        workflow_data = {
            "url": url,
            "steps": steps
        }

        file_path = filedialog.asksaveasfilename(
            title="Export Workflow",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if not file_path:
            return

        try:
            with open(file_path, 'w') as f:
                json.dump(workflow_data, f, indent=2)
            self.log_message(f"Workflow exported to {file_path}")
        except Exception as e:
            self.log_message(f"Error exporting workflow: {e}")