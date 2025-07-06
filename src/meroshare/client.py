"""
Meroshare client implementation using Selenium for browser automation.
"""

import logging
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType
import tempfile

from selenium.common.exceptions import ElementClickInterceptedException

logger = logging.getLogger(__name__)


class MeroshareClient:
    """Client for interacting with Meroshare platform using Selenium."""

    def __init__(self, username, password, dp_id, crn, transaction_pin,  headless=True):
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
        self.transaction_pin = transaction_pin
        self.headless = headless
        self.driver = None

    def _setup_driver(self):
        """Set up the Chrome WebDriver with appropriate options."""
        chrome_options = Options()
        temp_dir = tempfile.mkdtemp()
        if self.headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--remote-debugging-port=9222')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument(f'--user-data-dir={temp_dir}')

        # Use ChromeDriverManager with Chrome browser
        driver_path = ChromeDriverManager(
            chrome_type=ChromeType.CHROMIUM).install()
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
            # Increased timeout to 20 seconds
            wait = WebDriverWait(self.driver, 60)

            # Wait for the page to be fully loaded
            wait.until(
                EC.presence_of_element_located(
                    (By.CLASS_NAME, "select2-selection__rendered"))
            )

            # Click on DP dropdown to open it
            dp_dropdown = wait.until(
                EC.element_to_be_clickable(
                    (By.CLASS_NAME, "select2-selection__rendered"))
            )
            dp_dropdown.click()
            logger.info("Clicked on DP dropdown")

            # Wait for the search input to be visible and enter DP ID
            search_input = wait.until(
                EC.presence_of_element_located(
                    (By.CLASS_NAME, "select2-search__field"))
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
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[contains(text(), 'Login')]"))
            )
            login_button.click()
            logger.info("Clicked login button")

            # Wait for successful login by checking for logout icon
            wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "i.msi.msi-logout.header-menu__icon"))
            )
            logger.info("Successfully logged in to Meroshare")

        except Exception as e:
            logger.error(f"Failed to login: {str(e)}")
            if self.driver:
                self.driver.save_screenshot("login_error.png")
                logger.info(
                    "Saved screenshot of error state to login_error.png")
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
                    EC.element_to_be_clickable(
                        (By.XPATH, "//a[@href='#/asba']"))
                )
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", asba_link)
                time.sleep(0.3)
                try:
                    asba_link.click()
                except ElementClickInterceptedException:
                    logger.info("Click intercepted, using JavaScript click instead")
                    self.driver.execute_script("arguments[0].click();", asba_link)

                
                logger.info("Navigated to My ASBA section")

                # # Wait for the ASBA page to load
                # wait.until(
                #     EC.presence_of_element_located((By.CLASS_NAME, "asba-container"))
                # )
                # return
            else:
                raise ValueError(f"Unknown navigation element: {element}")

        except Exception as e:
            logger.error(f"Failed to navigate to {element}: {str(e)}")
            raise

    def getAvailableIPOS(self):
        if not self.driver:
            raise Exception("Browser not initialized. Please login first.")

        try:
            wait = WebDriverWait(self.driver, 10)

            # Wait for all IPO containers
            containers = wait.until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, "div.company-list")
                )
            )

            filtered_containers = []
            company_names = []

            for container in containers:
                try:
                    share_type = container.find_element(By.CSS_SELECTOR, "span[tooltip='Share Type']").text.strip()
                    share_group = container.find_element(By.CSS_SELECTOR, "span[tooltip='Share Group']").text.strip()

                    if share_type == "IPO" and share_group == "Ordinary Shares":
                        # Get company name for this container
                        company_name = container.find_element(By.CSS_SELECTOR, "span[tooltip='Company Name']").text.strip()

                        filtered_containers.append(container)
                        company_names.append(company_name)

                except Exception as e:
                    logger.warning(f"Error reading container info, skipping: {e}")

            logger.info("------------------------------------------")
            for index, name in enumerate(company_names, start=1):
                logger.info(f"{index}. {name}")
            logger.info("------------------------------------------")

            # Return the filtered containers for further processing (like clicking Apply)
            return filtered_containers

        except Exception as e:
            logger.error(f"Failed to get IPOs: {e}")
            raise

    def applyAvailableIPOS(self):
        if not self.driver:
            raise Exception("Browser not initialized. Please login first.")
    
        try:
            wait = WebDriverWait(self.driver, 10)

            containers = wait.until(
                EC.presence_of_all_elements_located(
                    (By.CSS_SELECTOR, "div.company-list"))
            )

            for container in containers:
                try:
                    share_type = container.find_element(
                        By.CSS_SELECTOR, "span[tooltip='Share Type']").text.strip()
                    share_group = container.find_element(
                        By.CSS_SELECTOR, "span[tooltip='Share Group']").text.strip()

                    if share_type == "IPO" and share_group == "Ordinary Shares":
                        try:
                            # Try to locate the Apply button inside the container
                            apply_button = container.find_element(
                                By.XPATH, ".//button[contains(@class, 'btn-issue') and .//i[contains(text(), 'Apply')]]"
                            )

                            print(not apply_button.is_displayed() or not apply_button.is_enabled())

                            # Optional: Check visibility and if it's enabled
                            if not apply_button.is_displayed() or not apply_button.is_enabled():
                                logger.info("Already Applied, skipping this IPO.")
                                continue

                            # Scroll into view
                            self.driver.execute_script("arguments[0].scrollIntoView();", apply_button)

                            # Wait until it's clickable
                            WebDriverWait(self.driver, 10).until(
                                EC.element_to_be_clickable((
                                    By.XPATH,
                                    ".//button[contains(@class, 'btn-issue') and .//i[contains(text(), 'Apply')]]"
                                ))
                            )

                            # Click the Apply button
                            apply_button.click()
                            print("[INFO] Clicked Apply on first Ordinary Share IPO.")

                            # Proceed to form filling
                            self.fillApplyForm()

                            break  # Exit after applying to first IPO

                        except Exception:
                            logger.info("Seems like already Applied")
                            continue  # Go to next IPO container

                except Exception as inner_e:
                    print(f"[WARN] Error in one container, skipping: {inner_e}")

        except Exception as e:
            logger.error(f"Testing this exception : {e}")
            raise Exception(f"Testing this exception : {e}")

    def fillApplyForm(self):
        if not self.driver:
            raise Exception("Browser not initialized. Please login first.")

        try:
            # Initialize with longer wait time
            wait = WebDriverWait(self.driver, 15)

            # Retry mechanism

            # 1. Wait for dropdown to be ready (Angular-specific wait)
            select_element = wait.until(
                lambda d: d.find_element(By.ID, "selectBank")
            )

            # 2. Click to open dropdown (may be needed for Angular)
            select_element.click()
            time.sleep(1)  # Brief pause for dropdown animation

            # 3. Find the option (using more robust XPath)
            option = wait.until(
                EC.presence_of_element_located(
                    (By.XPATH,
                     "//select[@id='selectBank']/option[@value='37']")
                )
            )

            option.click()

            time.sleep(1)

            account_number = wait.until(
                EC.presence_of_element_located(
                    (By.ID, "accountNumber")
                )
            )

            account_number.click()

            account_number_option = wait.until(EC.presence_of_element_located((
                By.XPATH,
                f"//select[@id='accountNumber']/option[@value={self.crn}]"
            )))

            account_number_option.click()

            applied_kitta = wait.until(EC.presence_of_element_located((
                By.ID, "appliedKitta"
            )))
            applied_kitta.clear()
            applied_kitta.send_keys("10")

            crnNumber = wait.until(EC.presence_of_element_located(
                (By.ID, "crnNumber")
            ))

            crnNumber.clear()

            crnNumber.send_keys(self.crn)

            disclaimer = wait.until(EC.presence_of_element_located(
                (By.ID, "disclaimer")
            ))

            disclaimer.click()

            button_locator = wait.until(EC.presence_of_element_located((
                By.CSS_SELECTOR, "button.btn.btn-gap.btn-primary[type='submit']")
            ))

            button_locator.click()

            transaction_pin_container = wait.until(EC.presence_of_element_located(
                (By.ID, "transactionPIN")
            ))

            transaction_pin_container.clear()

            transaction_pin_container.send_keys(self.transaction_pin)

            pin_submit = wait.until(EC.presence_of_element_located(
                (By.XPATH, "//button[span[text()='Apply ']]")
            ))

            pin_submit.click()

        except Exception as e:
            logger.error(f"Critical failure in bank selection: {e}")
            raise

    def close(self):
        """Close the browser and clean up resources."""
        if self.driver:
            self.driver.quit()
            self.driver = None
