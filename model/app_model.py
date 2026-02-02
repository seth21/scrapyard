from asyncio.windows_events import NULL
from tkinter import filedialog
import threading
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from tkinter import filedialog, messagebox
from urllib.parse import urljoin
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

from model.browser import SeleniumDriver
from model.engine import ScraperEngine
from model.xls_exporter import XlsExporter


class Model:
    scraped_data = []
    engine = None
    driver = None
    exporter = None

    def __init__(self):
        super().__init__()

        self.driver = SeleniumDriver()
        self.exporter = XlsExporter()
        self.engine = ScraperEngine()

    def stop(self):
        self.stop_event.set()

    def _stopped(self, output_queue):
        if self.stop_event.is_set():
            output_queue.put(("finish", "stopped"))
            return True
        return False
