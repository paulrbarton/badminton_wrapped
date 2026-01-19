"""
Selenium-based web scraper for Nottinghamshire Badminton League.
Handles cookie consent and page navigation.
"""
import time
import logging
import os
import ssl
from typing import Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

from config import (
    COOKIE_CONSENT_SELECTORS,
    PAGE_LOAD_TIMEOUT,
    IMPLICIT_WAIT,
    REQUEST_DELAY,
    HEADLESS,
    WINDOW_SIZE,
    USER_AGENT
)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BadmintonScraper:
    """Web scraper for badminton tournament data using Selenium."""
    
    def __init__(self):
        """Initialize the scraper with Selenium WebDriver."""
        self.driver = None
        self.cookie_consent_accepted = False
        
    def setup_driver(self) -> webdriver.Chrome:
        """Set up and return Chrome WebDriver with appropriate options."""
        logger.info("Setting up Chrome WebDriver...")
        
        chrome_options = Options()
        
        if HEADLESS:
            chrome_options.add_argument('--headless=new')
        
        chrome_options.add_argument(f'--window-size={WINDOW_SIZE[0]},{WINDOW_SIZE[1]}')
        chrome_options.add_argument(f'user-agent={USER_AGENT}')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        
        # Try to use Chrome with automatic driver detection
        try:
            driver = webdriver.Chrome(options=chrome_options)
            driver.implicitly_wait(IMPLICIT_WAIT)
            logger.info("Chrome WebDriver initialized successfully")
            return driver
        except Exception as e:
            logger.error(f"Failed to initialize Chrome WebDriver: {str(e)}")
            logger.info("Please ensure Chrome/Chromium browser is installed")
            logger.info("Or install ChromeDriver manually: brew install chromedriver")
            raise
    
    def accept_cookies(self) -> bool:
        """
        Attempt to accept cookie consent using multiple selector strategies.
        
        Returns:
            bool: True if cookies were accepted, False otherwise
        """
        if self.cookie_consent_accepted:
            return True
            
        logger.info("Attempting to accept cookie consent...")
        
        for selector in COOKIE_CONSENT_SELECTORS:
            try:
                # Determine selector type
                if selector.startswith('//'):
                    by = By.XPATH
                else:
                    by = By.CSS_SELECTOR
                
                # Wait for element and click
                element = WebDriverWait(self.driver, 3).until(
                    EC.element_to_be_clickable((by, selector))
                )
                logger.info(f"Found cookie consent button with selector: {selector}")
                element.click()
                time.sleep(3)  # Wait for modal to disappear and page to reload
                
                logger.info(f"Cookie consent accepted successfully!")
                self.cookie_consent_accepted = True
                return True
                
            except (TimeoutException, NoSuchElementException) as e:
                logger.debug(f"Selector '{selector}' not found: {type(e).__name__}")
                continue
        
        logger.warning("Could not find cookie consent button - may already be accepted")
        self.cookie_consent_accepted = True  # Assume accepted if button not found
        return False
    
    def get_page(self, url: str, wait_for_selector: Optional[str] = None) -> bool:
        """
        Navigate to a URL and optionally wait for a specific element.
        
        Args:
            url: The URL to navigate to
            wait_for_selector: CSS selector to wait for (optional)
            
        Returns:
            bool: True if page loaded successfully, False otherwise
        """
        try:
            logger.info(f"Navigating to: {url}")
            self.driver.get(url)
            
            # Accept cookies on first page load
            if not self.cookie_consent_accepted:
                self.accept_cookies()
            
            # Wait for specific element if provided
            if wait_for_selector:
                try:
                    WebDriverWait(self.driver, PAGE_LOAD_TIMEOUT).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, wait_for_selector))
                    )
                    logger.info(f"Element '{wait_for_selector}' found on page")
                except TimeoutException:
                    logger.warning(f"Timeout waiting for '{wait_for_selector}', but continuing anyway")
                    # Don't fail - the page might still have content
            
            # Respectful delay between requests
            time.sleep(REQUEST_DELAY)
            return True
            
        except Exception as e:
            logger.error(f"Error loading page {url}: {str(e)}")
            return False
    
    def get_page_source(self) -> str:
        """Return the current page's HTML source."""
        return self.driver.page_source
    
    def start(self):
        """Start the scraper by initializing the driver."""
        if self.driver is None:
            self.driver = self.setup_driver()
    
    def stop(self):
        """Stop the scraper and close the browser."""
        if self.driver:
            logger.info("Closing browser...")
            self.driver.quit()
            self.driver = None
            self.cookie_consent_accepted = False
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
