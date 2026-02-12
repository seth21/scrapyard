import queue
import threading

class Context:
    def __init__(self, view):
        super().__init__()
        self.queue = queue.Queue()
        self.view = view
        self.stop_event = threading.Event()
        self.next_page_selector = None
        self.next_js_mode = False
        self.global_state = {}
        self.page_state = {}
        self.repeat_stack = []

    def main_loop(self):
        self.poll_queue()

    def poll_queue(self):
        while not self.queue.empty():
            msg_type, payload = self.queue.get()
            if msg_type == "progress":
                self.view.progress_bar.set(payload)
            elif msg_type == "finish":
                self.running = False
                self.view.export_button.configure(state="normal")
                self.view.scrape_button.configure(state="normal")
                self.view.scrape_button.configure(text="Run Scraper", fg_color="blue")
            else:
                self.view.log_type_message(msg_type, payload)

        self.view.after(100, lambda: self.poll_queue())

    def stop(self):
        self.stop_event.set()

    def is_stopped(self, output_queue):
        if self.stop_event.is_set():
            output_queue.put(("finish", "stopped"))
            return True
        return False

    def is_stopped(self):
        if self.stop_event.is_set():
            return True
        return False

    def push_message(self, msg_type, payload):
        self.queue.put((msg_type, payload))

    def current_repeat_state(self):
        if not self.repeat_stack:
            return None
        return self.repeat_stack[-1]