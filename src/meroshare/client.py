"""
Meroshare client implementation using Selenium for browser automation.
"""

import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType

logger = logging.getLogger(__name__)

class MeroshareClient:
    """Client for interacting with Meroshare platform using Selenium."""
    
    def __init__(self, username, password, dp_id, crn, headless=False):
        """Initialize the Meroshare client.
        
        Args:
            username (str): Meroshare username
            password (str): Meroshare password
            dp_id (str): DP ID number
            crn (str): Customer Reference Number
            headless (bool): Whether to run browser in headless mode
        """
        self.username = username
        self.password = password
        self.dp_id = dp_id
        self.crn = crn
        self.headless = headless
        self.driver = None
        
    def _setup_driver(self):
        """Set up the Chrome WebDriver with appropriate options."""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--remote-debugging-port=9222')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        
        # Use ChromeDriverManager with Chrome browser
        driver_path = ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install()
        service = Service(driver_path)
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.maximize_window()
        
    def login(self):
        """Log in to Meroshare platform."""
        if not self.driver:
            self._setup_driver()
            
        try:
            # Navigate to login page
            self.driver.get('https://meroshare.cdsc.com.np/#/login')
            logger.info("Navigated to Meroshare login page")
            
            # Wait for the login form to be visible
            wait = WebDriverWait(self.driver, 60)  # Increased timeout to 20 seconds
            
            # Wait for the page to be fully loaded
            wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "select2-selection__rendered"))
            )
            
            # Click on DP dropdown to open it
            dp_dropdown = wait.until(
                EC.element_to_be_clickable((By.CLASS_NAME, "select2-selection__rendered"))
            )
            dp_dropdown.click()
            logger.info("Clicked on DP dropdown")
            
            # Wait for the search input to be visible and enter DP ID
            search_input = wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "select2-search__field"))
            )
            search_input.clear()
            search_input.send_keys(self.dp_id)
            search_input.send_keys(Keys.ENTER)
            logger.info(f"Selected DP ID: {self.dp_id}")
            
            # Enter username
            username_field = wait.until(
                EC.presence_of_element_located((By.NAME, "username"))
            )
            username_field.clear()
            username_field.send_keys(self.username)
            logger.info("Entered username")
            
            # Enter password
            password_field = wait.until(
                EC.presence_of_element_located((By.NAME, "password"))
            )
            password_field.clear()
            password_field.send_keys(self.password)
            logger.info("Entered password")
            
            # Click login button
            login_button = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Login')]"))
            )
            login_button.click()
            logger.info("Clicked login button")
            
            # Wait for successful login by checking for logout icon
            wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "i.msi.msi-logout.header-menu__icon"))
            )
            logger.info("Successfully logged in to Meroshare")
            
        except Exception as e:
            logger.error(f"Failed to login: {str(e)}")
            if self.driver:
                self.driver.save_screenshot("login_error.png")
                logger.info("Saved screenshot of error state to login_error.png")
                self.driver.quit()
            raise
            
    def navigate(self, element):
        """Navigate to a specific section in Meroshare.
        
        Args:
            element (str): The element to navigate to (e.g., 'asba', 'dashboard', etc.)
        """
        if not self.driver:
            raise Exception("Browser not initialized. Please login first.")
            
        try:
            wait = WebDriverWait(self.driver, 10)
            
            if element.lower() == 'asba':
                # Wait for and click the My ASBA link
                asba_link = wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//a[@href='#/asba']"))
                )
                asba_link.click()
                logger.info("Navigated to My ASBA section")
                
                # Wait for the ASBA page to load
                wait.until(
                    EC.presence_of_element_located((By.CLASS_NAME, "asba-container"))
                )
            else:
                raise ValueError(f"Unknown navigation element: {element}")
                
        except Exception as e:
            logger.error(f"Failed to navigate to {element}: {str(e)}")
            raise
            
    def close(self):
        """Close the browser and clean up resources."""
        if self.driver:
            self.driver.quit()
            self.driver = None
