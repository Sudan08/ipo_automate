"""
Meroshare client implementation using Selenium for browser automation.
"""

import logging
import random
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import tempfile

from selenium.common.exceptions import (
    ElementClickInterceptedException,
    NoSuchElementException,
    StaleElementReferenceException,
)

logger = logging.getLogger(__name__)


class MeroshareClient:
    """Client for interacting with Meroshare platform using Selenium."""

    # How often the Angular-populated dropdowns are re-read while waiting for
    # them to load and settle.
    POLL_INTERVAL = 0.5

    # A person reads a field, moves the mouse, and types - none of which happens
    # instantly. Filling the whole form in a few hundred milliseconds is the most
    # obvious tell that a script is driving the page, so every step is separated
    # by a randomised pause and every value is typed a character at a time. The
    # ranges below are seconds, scaled by `self.pace`.
    STEP_PAUSE = (0.8, 2.0)
    KEYSTROKE_PAUSE = (0.05, 0.18)

    def __init__(
        self,
        username,
        password,
        dp_id,
        crn,
        transaction_pin,
        headless=True,
        account_name=None,
        bank=None,
        bank_account=None,
        applied_kitta="10",
        dry_run=False,
        pace=1.0,
    ):
        """Initialize the Meroshare client.

        Args:
            username (str): Meroshare username
            password (str): Meroshare password
            dp_id (str): DP ID number
            crn (str): Customer Reference Number
            headless (bool): Whether to run browser in headless mode
            account_name (str): Optional label used to prefix log lines when
                running multiple accounts, for easier log reading.
            bank (str): Optional bank to apply through, matched against the
                bank dropdown by name (substring, case-insensitive) or by the
                option's value. Defaults to the only/first bank linked to the
                account.
            bank_account (str): Optional account number to apply with, matched
                the same way. Defaults to the only/first account of the bank.
            applied_kitta (str): Number of units to apply for. Defaults to 10.
            dry_run (bool): Fill the application form but stop before submitting
                it, so the bank/account selection can be verified without
                committing a real application.
            pace (float): Multiplier on every human-like pause between steps.
                1.0 is the normal pace, 2.0 is twice as slow and deliberate,
                0 removes the pauses entirely (fast, but the run looks like a
                script to MeroShare).
        """
        self.username = username
        self.password = password
        self.dp_id = dp_id
        self.crn = crn
        self.transaction_pin = transaction_pin
        self.headless = headless
        self.account_name = account_name
        self.bank = bank
        self.bank_account = bank_account
        self.applied_kitta = str(applied_kitta or "10")
        self.dry_run = dry_run
        self.pace = max(0.0, float(pace))
        self.driver = None

    def _log_prefix(self):
        return f"[{self.account_name}] " if self.account_name else ""

    def _setup_driver(self):
        """Set up the Chrome WebDriver with appropriate options."""
        chrome_options = Options()
        temp_dir = tempfile.mkdtemp()
        if self.headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--remote-debugging-port=9222")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument(f"--user-data-dir={temp_dir}")

        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.maximize_window()

    def login(self):
        """Log in to Meroshare platform."""
        if not self.driver:
            self._setup_driver()

        try:
            # Navigate to login page
            self.driver.get("https://meroshare.cdsc.com.np/#/login")
            logger.info("Navigated to Meroshare login page")

            # Wait for the login form to be visible
            # Increased timeout to 20 seconds
            wait = WebDriverWait(self.driver, 60)

            # Wait for the page to be fully loaded
            wait.until(
                EC.presence_of_element_located(
                    (By.CLASS_NAME, "select2-selection__rendered")
                )
            )

            # Click on DP dropdown to open it
            dp_dropdown = wait.until(
                EC.element_to_be_clickable(
                    (By.CLASS_NAME, "select2-selection__rendered")
                )
            )
            self._pause("opening the DP dropdown")
            dp_dropdown.click()
            logger.info("Clicked on DP dropdown")

            # Wait for the search input to be visible and enter DP ID
            search_input = wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "select2-search__field"))
            )
            self._type(search_input, self.dp_id, "DP ID")
            self._pause("confirming the DP")
            search_input.send_keys(Keys.ENTER)
            logger.info(f"Selected DP ID: {self.dp_id}")

            # Enter username
            username_field = wait.until(
                EC.presence_of_element_located((By.NAME, "username"))
            )
            self._pause("the username field")
            self._type(username_field, self.username, "username")
            logger.info("Entered username")

            # Enter password
            password_field = wait.until(
                EC.presence_of_element_located((By.NAME, "password"))
            )
            self._pause("the password field")
            self._type(password_field, self.password, "password")
            logger.info("Entered password")

            # Click login button
            login_button = wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[contains(text(), 'Login')]")
                )
            )
            self._pause("submitting the login form")
            login_button.click()
            logger.info("Clicked login button")

            # Wait for successful login by checking for logout icon
            wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "i.msi.msi-logout.header-menu__icon")
                )
            )
            logger.info(f"{self._log_prefix()}Successfully logged in to Meroshare")

        except Exception as e:
            logger.error(f"{self._log_prefix()}Failed to login: {str(e)}")
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
            if element.lower() == "asba":
                # Wait for and click the My ASBA link
                asba_link = wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//a[@href='#/asba']"))
                )
                self.driver.execute_script(
                    "arguments[0].scrollIntoView({block: 'center'});", asba_link
                )
                self._pause("opening My ASBA")
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
            # Wait briefly for the page to settle, then use find_elements which
            # safely returns [] instead of raising TimeoutException when nothing found.
            time.sleep(3)
            containers = self.driver.find_elements(By.CSS_SELECTOR, "div.company-list")

            if len(containers) == 0:
                logger.info(f"{self._log_prefix()}No IPOs are currently available.")
                return []

            filtered_containers = []
            company_names = []

            for container in containers:
                try:
                    share_type = container.find_element(
                        By.CSS_SELECTOR, "span[tooltip='Share Type']"
                    ).text.strip()
                    share_group = container.find_element(
                        By.CSS_SELECTOR, "span[tooltip='Share Group']"
                    ).text.strip()

                    if share_type == "IPO" and share_group == "Ordinary Shares":
                        # Get company name for this container
                        company_name = container.find_element(
                            By.CSS_SELECTOR, "span[tooltip='Company Name']"
                        ).text.strip()

                        filtered_containers.append(container)
                        company_names.append(company_name)

                except NoSuchElementException:
                    logger.warning("Error reading container info, skipping.")

            if not filtered_containers:
                logger.info("No IPOs are currently available.")
                return []

            logger.info("------------------------------------------")
            for index, name in enumerate(company_names, start=1):
                logger.info(f"{index}. {name}")
            logger.info("------------------------------------------")

            # Return the filtered containers for further processing (like clicking Apply)
            return filtered_containers

        except Exception as e:
            logger.error(f"{self._log_prefix()}Failed to get IPOs: {e}")
            raise

    def applyAvailableIPOS(self):
        """Apply for every open Ordinary Share IPO that has not been applied for.

        Returns:
            int: how many IPOs an application was submitted for.
        """
        if not self.driver:
            raise Exception("Browser not initialized. Please login first.")

        applied_count = 0

        # Use find_elements so an empty page returns [] instead of raising TimeoutException
        containers = self.driver.find_elements(By.CSS_SELECTOR, "div.company-list")

        if len(containers) == 0:
            logger.info(f"{self._log_prefix()}No IPOs are currently available.")
            return 0

        for container in containers:
            try:
                share_type = container.find_element(
                    By.CSS_SELECTOR, "span[tooltip='Share Type']"
                ).text.strip()
                share_group = container.find_element(
                    By.CSS_SELECTOR, "span[tooltip='Share Group']"
                ).text.strip()
                company_name = container.find_element(
                    By.CSS_SELECTOR, "span[tooltip='Company Name']"
                ).text.strip()
            except NoSuchElementException:
                logger.warning(
                    f"{self._log_prefix()}Could not read a company row, skipping it."
                )
                continue

            if share_type != "IPO" or share_group != "Ordinary Shares":
                continue

            # A missing / disabled Apply button is the normal "already applied"
            # case; only that is treated as skippable. Anything that goes wrong
            # afterwards is a real failure and must propagate.
            try:
                apply_button = container.find_element(
                    By.XPATH,
                    ".//button[contains(@class, 'btn-issue') and .//i[contains(text(), 'Apply')]]",
                )
            except NoSuchElementException:
                logger.info(
                    f"{self._log_prefix()}{company_name}: no Apply button "
                    f"(already applied), skipping."
                )
                continue

            if not apply_button.is_displayed() or not apply_button.is_enabled():
                logger.info(
                    f"{self._log_prefix()}{company_name}: Apply button disabled "
                    f"(already applied), skipping."
                )
                continue

            self.driver.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", apply_button
            )
            self._wait(10).until(EC.element_to_be_clickable(apply_button))
            self._pause(f"clicking Apply for {company_name}")
            try:
                apply_button.click()
            except ElementClickInterceptedException:
                self.driver.execute_script("arguments[0].click();", apply_button)
            logger.info(f"{self._log_prefix()}Clicked Apply for {company_name}")

            self.fillApplyForm()
            applied_count += 1
            logger.info(f"{self._log_prefix()}Submitted application for {company_name}")
            break  # Exit after applying to the first open IPO

        return applied_count

    def _pause(self, what=None, bounds=None):
        """Sleep for a randomised, human-length beat between two steps.

        Randomised rather than fixed: a constant delay is just as machine-like as
        no delay at all, only slower.
        """
        if not self.pace:
            return
        low, high = bounds or self.STEP_PAUSE
        delay = random.uniform(low, high) * self.pace
        if what:
            logger.debug(f"{self._log_prefix()}Pausing {delay:.1f}s before {what}")
        time.sleep(delay)

    def _type(self, element, text, what=None):
        """Type into a field the way a person does - one key at a time.

        `send_keys(whole_string)` lands the entire value in a single input event,
        which no keyboard can produce.
        """
        element.clear()
        if not self.pace:
            element.send_keys(text)
            return
        for character in str(text):
            element.send_keys(character)
            time.sleep(random.uniform(*self.KEYSTROKE_PAUSE) * self.pace)
        if what:
            logger.debug(f"{self._log_prefix()}Typed {what}")

    def _wait(self, timeout=15):
        """A WebDriverWait that tolerates Angular re-rendering elements mid-poll."""
        return WebDriverWait(
            self.driver,
            timeout,
            ignored_exceptions=(
                NoSuchElementException,
                StaleElementReferenceException,
            ),
        )

    @staticmethod
    def _real_options(select):
        """Return only the options of a <select> that are genuine choices.

        MeroShare's dropdowns are Angular-bound and start out holding just a
        placeholder row - "Select Bank", or the "? undefined:undefined ?" option
        Angular inserts while the ngModel is unset - so those must be filtered
        out before deciding whether the data has actually arrived.
        """
        real = []
        for option in select.options:
            value = (option.get_attribute("value") or "").strip()
            text = (option.text or "").strip()
            if not value or value.startswith("?") or value.lower() in ("null", "undefined"):
                continue
            if text.lower().startswith("select "):
                continue
            real.append(option)
        return real

    def _option_signature(self, options):
        """A comparable fingerprint of a dropdown's current real options."""
        return [
            (
                (o.get_attribute("value") or "").strip(),
                (o.text or "").strip(),
            )
            for o in options
        ]

    def _wait_for_options(self, element_id, description, timeout=30):
        """Wait until an Angular-populated <select> has finished loading.

        MeroShare fetches the bank list, and then each bank's accounts, over the
        network. A dropdown therefore goes through empty -> partially populated /
        still holding the previous bank's rows -> final. Reading it the moment it
        is merely non-empty can pick up rows that Angular then replaces, which
        leaves the form holding an account the server rejects - the application
        never gets recorded even though every click "succeeded".

        Requiring the option list to come back identical on two consecutive polls
        means the fetch that produced it has settled, and requiring the element to
        be enabled means Angular is no longer blocking it while loading.

        Returns:
            tuple: (Select, list of real options) once the list is stable.
        """
        deadline = time.time() + timeout
        previous = None
        while time.time() < deadline:
            try:
                element = self.driver.find_element(By.ID, element_id)
                if not element.is_enabled():
                    previous = None
                    time.sleep(self.POLL_INTERVAL)
                    continue
                select = Select(element)
                options = self._real_options(select)
                signature = self._option_signature(options)
            except (NoSuchElementException, StaleElementReferenceException):
                previous = None
                time.sleep(self.POLL_INTERVAL)
                continue

            if signature and signature == previous:
                return select, options

            previous = signature
            time.sleep(self.POLL_INTERVAL)

        raise RuntimeError(
            f"{description} dropdown (#{element_id}) never finished loading its "
            f"options within {timeout}s."
        )

    def _verify_selection(self, element_id, description, expected_value, timeout=10):
        """Confirm the browser really is holding the option we asked for.

        Angular can reset a <select> right after it is set - when the change it
        listens for triggers another reload of the same list - so a select call
        that returned cleanly is not proof the value stuck. Checking the selected
        option afterwards is what turns a silent no-op into a loud failure.
        """
        deadline = time.time() + timeout
        current = None
        while time.time() < deadline:
            try:
                select = Select(self.driver.find_element(By.ID, element_id))
                current = (
                    select.first_selected_option.get_attribute("value") or ""
                ).strip()
            except (NoSuchElementException, StaleElementReferenceException):
                current = None
            if current == expected_value:
                return
            time.sleep(self.POLL_INTERVAL)

        raise RuntimeError(
            f"{description} would not stay selected: asked for "
            f"'{expected_value}', the form is holding '{current}'."
        )

    def _select_dropdown_option(self, element_id, description, preferred=None):
        """Pick an option from an Angular-populated <select> by name, not by a
        hardcoded option value.

        Bank ids and bank-account ids are per-account and assigned by MeroShare,
        so they cannot be hardcoded or derived from the CRN. The options are read
        from the page instead: `preferred` is matched against each option's
        visible text (case-insensitive substring) or its exact value, and when no
        preference is configured the single available option is used.

        Args:
            element_id (str): id of the <select> element.
            description (str): human name used in logs and error messages.
            preferred (str): optional bank / account name or option value.

        Returns:
            str: the visible text of the option that was selected.
        """
        self._wait().until(EC.presence_of_element_located((By.ID, element_id)))
        select, options = self._wait_for_options(element_id, description)

        available = [
            f"{o.get_attribute('value')}={(o.text or '').strip()}" for o in options
        ]
        logger.info(
            f"{self._log_prefix()}Available {description}(s): {', '.join(available)}"
        )

        chosen = None
        if preferred:
            needle = str(preferred).strip().lower()
            for option in options:
                value = (option.get_attribute("value") or "").strip().lower()
                text = (option.text or "").strip().lower()
                if needle == value or needle in text:
                    chosen = option
                    break
            if chosen is None:
                raise RuntimeError(
                    f"No {description} matching '{preferred}'. "
                    f"Available: {', '.join(available)}"
                )
        else:
            chosen = options[0]
            if len(options) > 1:
                logger.warning(
                    f"{self._log_prefix()}{len(options)} {description}s linked to this "
                    f"account and none configured; using the first one. Set it "
                    f"explicitly in accounts.json to choose."
                )

        chosen_text = (chosen.text or "").strip()
        chosen_value = (chosen.get_attribute("value") or "").strip()
        self._pause(f"picking the {description}")
        select.select_by_value(chosen_value)
        self._verify_selection(element_id, description, chosen_value)
        logger.info(f"{self._log_prefix()}Selected {description}: {chosen_text}")
        return chosen_text

    def _confirm_submission(self, timeout=45):
        """Wait for MeroShare to actually acknowledge the application.

        Clicking Apply only starts a request; the browser used to be torn down in
        the caller's `finally` immediately afterwards, so a rejected - or still
        in-flight - application was reported as a success. The PIN dialog closing
        is what marks the request as done, and the toast carries the verdict.
        """
        deadline = time.time() + timeout
        message = None
        while time.time() < deadline:
            message = self._read_toast()
            if message:
                break
            if not self._pin_dialog_open():
                break
            time.sleep(self.POLL_INTERVAL)

        if message:
            lowered = message.lower()
            if any(
                word in lowered
                for word in ("error", "fail", "invalid", "incorrect", "cannot")
            ):
                raise RuntimeError(f"MeroShare rejected the application: {message}")
            logger.info(f"{self._log_prefix()}MeroShare responded: {message}")
            return

        if self._pin_dialog_open():
            raise RuntimeError(
                "The transaction PIN dialog is still open after Apply - the "
                "application was not submitted."
            )

        logger.info(
            f"{self._log_prefix()}Application submitted (dialog closed, no message "
            f"shown)."
        )

    def _read_toast(self):
        """Text of any toast/alert MeroShare is currently showing, if any."""
        selectors = (
            "div.toast-message",
            "div.toast-title",
            "div[class*='toast']",
            "div.alert",
        )
        for selector in selectors:
            try:
                for element in self.driver.find_elements(By.CSS_SELECTOR, selector):
                    if element.is_displayed():
                        text = (element.text or "").strip()
                        if text:
                            return text
            except StaleElementReferenceException:
                continue
        return None

    def _pin_dialog_open(self):
        """Whether the transaction PIN dialog is still on screen."""
        try:
            return any(
                element.is_displayed()
                for element in self.driver.find_elements(By.ID, "transactionPIN")
            )
        except StaleElementReferenceException:
            return True

    def fillApplyForm(self):
        """Fill and submit the IPO application form for the open share."""
        if not self.driver:
            raise Exception("Browser not initialized. Please login first.")

        try:
            wait = self._wait(15)

            self._select_dropdown_option("selectBank", "bank", self.bank)

            # Picking a bank starts a fetch for that bank's accounts, so the
            # account dropdown is waited on until that fetch settles rather than
            # slept on for a fixed second.
            self._select_dropdown_option(
                "accountNumber", "bank account", self.bank_account
            )

            applied_kitta = wait.until(
                EC.element_to_be_clickable((By.ID, "appliedKitta"))
            )
            self._pause("the applied kitta field")
            self._type(applied_kitta, self.applied_kitta, "applied kitta")

            crnNumber = wait.until(EC.element_to_be_clickable((By.ID, "crnNumber")))
            self._pause("the CRN field")
            self._type(crnNumber, self.crn, "CRN")

            disclaimer = wait.until(EC.element_to_be_clickable((By.ID, "disclaimer")))
            self._pause("ticking the disclaimer")
            disclaimer.click()

            if self.dry_run:
                logger.info(
                    f"{self._log_prefix()}Dry run: form filled, stopping before submit."
                )
                self._save_debug_screenshot("apply_form_dryrun")
                return

            button_locator = wait.until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, "button.btn.btn-gap.btn-primary[type='submit']")
                )
            )
            self._pause("submitting the form")
            button_locator.click()

            transaction_pin_container = wait.until(
                EC.element_to_be_clickable((By.ID, "transactionPIN"))
            )
            self._pause("the transaction PIN field")
            self._type(transaction_pin_container, self.transaction_pin, "transaction PIN")

            pin_submit = wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[span[text()='Apply ']]")
                )
            )
            self._pause("confirming the application")
            pin_submit.click()

            self._confirm_submission()

        except Exception as e:
            logger.error(f"{self._log_prefix()}Failed to fill the application form: {e}")
            self._save_debug_screenshot("apply_form_error")
            raise

    def _save_debug_screenshot(self, prefix):
        """Best-effort screenshot of the current page, for diagnosing failures."""
        if not self.driver:
            return
        suffix = f"_{self.account_name}" if self.account_name else ""
        path = f"{prefix}{suffix}.png"
        try:
            self.driver.save_screenshot(path)
            logger.info(f"{self._log_prefix()}Saved screenshot of error state to {path}")
        except Exception as e:
            logger.warning(f"{self._log_prefix()}Could not save screenshot: {e}")

    def close(self):
        """Close the browser and clean up resources."""
        if self.driver:
            self.driver.quit()
            self.driver = None
            logger.info(f"{self._log_prefix()}Closed browser session")
