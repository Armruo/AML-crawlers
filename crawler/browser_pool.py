import logging
import queue
import threading
import undetected_chromedriver as uc
from typing import List

logger = logging.getLogger(__name__)

class BrowserPool:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = super(BrowserPool, cls).__new__(cls)
        return cls._instance

    def __init__(self, pool_size: int = 3):
        if not hasattr(self, 'initialized'):
            self.pool_size = pool_size
            self.browser_queue = queue.Queue()
            self.active_browsers: List[uc.Chrome] = []
            self.initialize_pool()
            self.initialized = True

    def initialize_pool(self):
        """Initialize the browser pool with the specified number of browsers"""
        for _ in range(self.pool_size):
            try:
                browser = self._create_browser()
                self.browser_queue.put(browser)
                self.active_browsers.append(browser)
            except Exception as e:
                logger.error(f"Error creating browser: {str(e)}")

    def _create_browser(self) -> uc.Chrome:
        """Create a new browser instance with optimized settings"""
        options = uc.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-notifications')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-infobars')
        
        browser = uc.Chrome(options=options)
        browser.implicitly_wait(10)
        return browser

    def get_browser(self) -> uc.Chrome:
        """Get a browser from the pool"""
        try:
            return self.browser_queue.get(timeout=30)
        except queue.Empty:
            logger.warning("Browser pool exhausted, creating new browser")
            browser = self._create_browser()
            self.active_browsers.append(browser)
            return browser

    def return_browser(self, browser: uc.Chrome):
        """Return a browser to the pool"""
        if browser in self.active_browsers:
            self.browser_queue.put(browser)

    def close_all(self):
        """Close all browser instances"""
        while self.active_browsers:
            browser = self.active_browsers.pop()
            try:
                browser.quit()
            except Exception as e:
                logger.error(f"Error closing browser: {str(e)}")
