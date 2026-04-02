from tkinter import filedialog, messagebox
import pandas as pd

from model.context import Context


class XlsExporter():
    def __init__(self):
        super().__init__()

    def export_to_excel(self, scraped_data, ctx:Context) -> None:
        if not scraped_data:
            return

        # Remove internal _skip_restore column before export
        for row in scraped_data:
            row.pop('_skip_restore', None)

        #Ask user where to save
        file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
        if file_path:
            try:
                df = pd.DataFrame(scraped_data)
                df.to_excel(file_path, index=False)
                ctx.push_message("done", f"Data saved to {file_path}")
                messagebox.showinfo("Success", "Data exported successfully!")
            except Exception as e:
                ctx.push_message("error", "Could not export data!")
                messagebox.showerror("Error", f"Could not save file: {e}")