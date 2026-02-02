import customtkinter as ct
from tkinter import ttk

class FlowView(ct.CTkFrame):

    tree:ttk.Treeview = None
    step_map = {}
    root_id = 0

    def __init__(self, master=None):
        super().__init__(master)

        # Style the Treeview to match Dark Mode
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="#2b2b2b", fieldbackground="#2b2b2b", foreground="white", rowheight=25)
        style.map('Treeview', background=[('selected', '#1f538d')])

        self.tree = ttk.Treeview(master, selectmode="browse")
        self.tree.pack(fill="both", expand=True, padx=5, pady=5)
        self.tree.heading("#0", text="Workflow Steps (Structure)", anchor="w")
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)

        # Initialize Root
        self.root_id = self.tree.insert("", "end", text="START", open=True)
        self.step_map[self.root_id] = {"type": "root", "children": []}

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
        if data['type'] == 'loop':
            self.create_prop_entry("Limit:", "limit", data)

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

    def create_prop_checkbox(self, label_text, key, data_dict):
        def checkbox_event():
            data_dict[key] = checkbox.get()

        value = data_dict.get(key, 0)
        checkbox = ct.CTkCheckBox(self.props_container, text=label_text, command=checkbox_event)
        if value:
            checkbox.select()
        # checkbox..insert(0, data_dict.get(key, ""))
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
            if p_data['type'] == 'extract':
                # If Extract selected, add to its parent instead
                parent_id = self.tree.parent(parent_id)
        else:
            parent_id = self.root_id

        # Insert Item
        text_map = {"extract": "📄 Extract Data", "loop": "🔁 For Each Element", "visit": "🔗 Visit Link"}
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
            if data['type'] in ['loop', 'visit']:
                step_config['children'] = self.build_config_recursive(child_id)
            if data['type'] in ['loop']:
                step_config['limit'] = data.get('limit', 0)
            if data['type'] == 'extract':
                step_config['sep'] = data.get('sep', ',')
                step_config['multi'] = data.get('multi', 0)
            steps.append(step_config)
        return steps


