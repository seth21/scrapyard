from model.app_model import Model
from model.context import Context
from model.browser import SeleniumDriver
from view.app_view import View
import threading
import queue

class Controller:
    def __init__(self):
        #Initialize model
        self.model = Model()
        #Initialize view
        self.view = View()
        self.queue = queue.Queue()
        #Bind view input here
        self.view.scrape_button.configure(command=self.run_job)
        self.view.export_button.configure(command=self.export_data)

        # Start polling queue immediately
        self.context = Context(self.view)
        self.context.main_loop()
        self.running = False

    def run(self):
        self.view.mainloop()

    def run_job(self):
        url = self.view.url_entry.get()
        if not url:
            self.queue.put(("error", "No URL provided."))
            return

        # Build Scraper Config
        steps = self.view.build_config_recursive(self.view.root_id)

        # Run in Thread
        if not self.running:
            self.view.start_progress()
            threading.Thread(target=self._run_thread, args=(steps, url), daemon=True).start()
            self.view.scrape_button.configure(text="Stop Scraper", fg_color="red")
            self.running = True
        else:
            self.view.log_type_message("warning", "Stopping scraper!")
            self.view.scrape_button.configure(state="disabled")
            self.context.stop()

    def export_data(self):
        data = self.model.engine.results
        self.model.exporter.export_to_excel(data, self.context)

    def _run_thread(self, steps, url):
        if not self.model.driver.is_alive():
            self.model.driver = SeleniumDriver()
        data = self.model.engine.run(steps, url, self.model.driver, self.context)
        self.scraped_data = data  # Store for export
        self.view.stop_progress()
        self.view.scrape_button.configure(
            text="Run Scraper",
            fg_color=self.view.scrape_button_default_color,
            state="normal"
        )
        self.running = False
        if data:
            self.view.export_button.configure(state="normal")