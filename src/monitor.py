import sys
from datetime import datetime
import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from src.models.course import Course
from src.utils.browser_utils import get_text_from_cell, determine_status
from src.utils.telegram_utils import TelegramNotifier
from dotenv import load_dotenv
import json

class RegistrationMonitor:
    def __init__(self):
        load_dotenv()

        # Configure Chrome options for headless operation
        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')

        # Initialize the webdriver and previous state
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 120)  # 120 second timeout
        self.json_file = "course_states.json"
        self.previous_states = self.load_previous_states()  # Load state from JSON

        # Initialize Telegram notifier
        self.notifier = TelegramNotifier()

        # Add flag to track initial setup
        self.is_initialized = False

    @staticmethod
    def unified_input(prompt):
        """
        A flexible input function that works both in Docker containers with /dev/tty and in Python shells.
        """
        if os.path.exists('/dev/tty'):  # Check if /dev/tty is available
            try:
                with open('/dev/tty', 'r') as tty:
                    sys.stdout.write(prompt)
                    sys.stdout.flush()
                    return tty.readline().strip()
            except Exception as e:
                print(f"Error reading from /dev/tty: {e}")
        # Fallback to standard input if /dev/tty is not available
        return input(prompt)


    def load_previous_states(self):
        """Load previous course states from a JSON file."""
        if os.path.exists(self.json_file):
            with open(self.json_file, 'r') as f:
                try:
                    data = json.load(f)
                    print(f"Loaded previous states from {self.json_file}: {data}")
                    return data
                except json.JSONDecodeError:
                    print("Error decoding JSON file. Starting with empty state.")
                    return {}
        print("No existing JSON file found. Starting with empty state.")
        return {}

    def save_current_states(self, current_states):
        """Save current course states to a JSON file."""
        try:
            with open(self.json_file, 'w') as f:
                json.dump(current_states, f, indent=4)
            print(f"Successfully saved current states to {self.json_file}.")
        except Exception as e:
            print(f"Error saving JSON file: {e}")

    def check_for_changes(self, current_states):
        """Compare current states with previous states and detect changes."""
        changes = []

        for crn, current in current_states.items():
            if crn in self.previous_states:
                # Compare the status of the current course with the previous state
                previous = self.previous_states[crn]
                if current['status'] != previous['status']:
                    changes.append({
                        'crn': crn,
                        'subject': current['subject'],
                        'course_num': current['course_num'],
                        'title': current['title'],
                        'instructor': current['instructor'],
                        'old_status': previous['status'],
                        'new_status': current['status']
                    })
            else:
                # New course detected
                changes.append({
                    'crn': crn,
                    'subject': current['subject'],
                    'course_num': current['course_num'],
                    'title': current['title'],
                    'instructor': current['instructor'],
                    'old_status': 'Not tracked',
                    'new_status': current['status']
                })

        return changes

    def start_login_process(self):
        """Navigate directly to MyMohawk and handle Microsoft login with 2FA"""
        try:
            # Configure Chrome to handle POST requests properly
            self.driver.execute_cdp_cmd('Network.enable', {})

            # Go directly to MyMohawk
            print("Step 1: Navigating to MyMohawk login page...")
            self.driver.get("https://mymohawk.mohawkcollege.ca/")

            # Wait for email input
            print("Step 2: Entering email...")
            email_input = self.wait.until(
                EC.presence_of_element_located((
                    By.XPATH,
                    "//input[@type='email'] | //input[@name='loginfmt']"
                ))
            )
            email_input.clear()
            email_input.send_keys(os.environ.get('MOHAWK_EMAIL'))

            # Click Next
            next_button = self.wait.until(
                EC.element_to_be_clickable((
                    By.XPATH,
                    "//input[@type='submit'] | //input[@id='idSIButton9']"
                ))
            )
            next_button.click()
            time.sleep(2)  # Allow for transition

            # Wait for password field
            print("Step 3: Entering password...")
            password_input = self.wait.until(
                EC.presence_of_element_located((
                    By.XPATH,
                    "//input[@type='password'] | //input[@name='passwd']"
                ))
            )
            password_input.clear()
            password_input.send_keys(os.environ.get('MOHAWK_PASSWORD'))

            # Click Sign in
            signin_button = self.wait.until(
                EC.element_to_be_clickable((
                    By.XPATH,
                    "//input[@type='submit'] | //input[@id='idSIButton9']"
                ))
            )
            signin_button.click()
            time.sleep(2)  # Allow for transition

            # Handle 2FA method selection
            print("Step 4: Handling 2FA method selection...")
            try:
                # Look for and click the text verification option
                text_option = self.wait.until(
                    EC.presence_of_element_located((
                        By.XPATH,
                        "//div[contains(text(), 'Text')] | //button[contains(text(), 'Text')]"
                    ))
                )
                text_option.click()
                print("Selected text verification option")

            except:
                print("No 2FA method selection found, continuing to code entry...")

            # Wait for verification code input
            print("Step 5: Entering 2FA code...")
            code_input = self.wait.until(
                EC.presence_of_element_located((
                    By.XPATH,
                    "//input[@name='otc'] | //input[contains(@aria-label, 'Enter code')]"
                ))
            )

            # Get verification code from user
            verification_code = self.unified_input("Enter the 2FA code sent to your phone: ")
            code_input.clear()
            code_input.send_keys(verification_code)

            # Click Verify
            verify_button = self.wait.until(
                EC.element_to_be_clickable((
                    By.XPATH,
                    "//input[@type='submit'] | //button[contains(text(), 'Verify')] | //input[@id='idSubmit_SAOTCC_Continue']"
                ))
            )
            verify_button.click()

            # Handle "Stay signed in?" prompt
            print("Step 6: Handling 'Stay signed in' prompt...")
            try:
                stay_signed_in = self.wait.until(
                    EC.element_to_be_clickable((
                        By.XPATH,
                        "//input[@id='idSIButton9'] | //input[@value='Yes']"
                    ))
                )
                stay_signed_in.click()
            except:
                print("No 'Stay signed in' prompt found, continuing...")

            # Wait for successful redirect
            print("Step 7: Waiting for successful login redirect...")
            self.wait.until(
                lambda driver: "mymohawk.mohawkcollege.ca/mymohawk-college/Home" in driver.current_url
            )
            print("Successfully logged in!")
            return True

        except TimeoutException as e:
            print(f"Timeout during login process: {str(e)}")
            self.driver.save_screenshot('timeout_error.png')
            self.notifier.send_message(f"⚠️ Login timeout error: {str(e)}")
            return False
        except Exception as e:
            print(f"Error during login process: {str(e)}")
            self.driver.save_screenshot('general_error.png')
            self.notifier.send_message(f"⚠️ Login error: {str(e)}")
            return False

    def monitor_courses(self, interval=600):
        """Main monitoring loop."""
        try:
            print("\nStarting course monitoring...")
            print("Press Ctrl+C to stop monitoring")

            # Perform initial setup if not done
            if not self.is_initialized:
                if not self.start_login_process() or not self.navigate_to_registration():
                    raise Exception("Failed to initialize monitoring")
                self.is_initialized = True

            # Load previously saved states from JSON on startup
            self.previous_states = self.load_previous_states()
            print(f"Loaded previous states on startup: {self.previous_states}")

            while True:
                try:
                    print(f"\nChecking courses at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}...")
                    self.notifier.send_message("Course Monitoring Started Successfully")

                    # Parse current course information
                    current_states = self.parse_course_info()

                    # Compare the loaded states with the current states
                    if self.previous_states:
                        changes = self.check_for_changes(current_states)
                        if changes:
                            print(f"Detected changes: {changes}")
                            self.notifier.alert_changes(changes)
                    else:
                        print("No previous states available for comparison.")

                    # Save current states to JSON
                    self.save_current_states(current_states)

                    # Update the previous states for the next iteration
                    self.previous_states = current_states

                    # Wait before the next check
                    print(f"Waiting {interval} seconds before next check...")
                    time.sleep(interval)

                except TimeoutException:
                    print("Page refresh timeout, attempting to reinitialize navigation...")
                    self.navigate_to_home_and_restart()

        except KeyboardInterrupt:
            print("\nStopping course monitor...")
            self.notifier.send_message("ℹ️ Course monitor stopped by user")

        except Exception as e:
            print(f"An error occurred in monitoring loop: {str(e)}")
            self.notifier.send_message(f"⚠️ Error in course monitor: {str(e)}")
            raise

        finally:
            self.close()

    def navigate_to_registration(self):
        """Navigate to the registration page after successful login"""
        try:
            # Navigate to the registration tab
            self.driver.get("https://mymohawk.mohawkcollege.ca/mymohawk-college/Registration")

            # Wait for the "Choose or change my timetable" link and click it
            timetable_link = self.wait.until(
                EC.presence_of_element_located((
                    By.XPATH,
                    "//a[contains(@href, 'wwskregs.P_WebRegs')]"
                ))
            )
            timetable_link.click()

            # Wait for new tab to open and switch to it
            self.wait.until(lambda driver: len(driver.window_handles) > 1)
            self.driver.switch_to.window(self.driver.window_handles[-1])

            # Wait for and click the "Submit to Confirm" button
            submit_button = self.wait.until(
                EC.element_to_be_clickable((
                    By.XPATH,
                    "//input[@type='submit'][@value='Submit to Confirm']"
                ))
            )
            submit_button.click()

            # Wait for and click the "559" span
            span_559 = self.wait.until(
                EC.element_to_be_clickable((
                    By.XPATH,
                    "//span[@class='textLargeCentered'][text()='559']"
                ))
            )
            span_559.click()

            # Wait for and click the "CONTINUE" button
            continue_button = self.wait.until(
                EC.element_to_be_clickable((
                    By.XPATH,
                    "//input[@type='submit'][@value='CONTINUE']"
                ))
            )
            continue_button.click()

            print("Successfully navigated through all registration steps!")
            return True

        except TimeoutException:
            print("Timeout waiting for one of the navigation elements.")
            return False
        except Exception as e:
            print(f"Error navigating to registration: {str(e)}")
            return False

    def navigate_to_home_and_restart(self):
        """Navigate back to the /home page and restart navigation to registration"""
        try:
            # Navigate to the home page
            print("Navigating back to the /home page...")
            self.driver.get("https://mymohawk.mohawkcollege.ca/mymohawk-college/Home")

            # Wait for the home page to load
            self.wait.until(EC.presence_of_element_located((By.XPATH, "//a[contains(text(), 'Registration')]")))

            # Reinitialize navigation to the registration page
            print("Reinitializing navigation to the registration page...")
            if not self.navigate_to_registration():
                raise Exception("Failed to navigate to the registration page")
        except Exception as e:
            print(f"Error during navigation reset: {str(e)}")
            self.notifier.send_message(f"⚠️ Error during navigation reset: {str(e)}")
            raise


    def parse_course_info(self):
        """Parse course information using the more robust parsing logic."""
        courses = []
        try:
            # Find all course rows
            rows = self.driver.find_elements(By.XPATH,
                                             "//tr[contains(@class, 'RegPageHeader') or contains(@class, 'RegPageHeaderWhite')]")
            print(f"\nProcessing {len(rows)} rows...")

            for row in rows:
                try:
                    # Skip header rows
                    if "CRN" in row.text:
                        continue

                    # Get CRN (cell 3) and validate
                    crn = get_text_from_cell(row, 3)
                    if not crn or not crn.isdigit():
                        continue

                    course = Course(
                        subject=get_text_from_cell(row, 4),
                        course_num=get_text_from_cell(row, 5),
                        title=get_text_from_cell(row, 6, get_link_text=True),
                        crn=crn,
                        status=determine_status(row),
                        instructor=get_text_from_cell(row, 9),
                        campus=get_text_from_cell(row, 7, get_link_text=True),
                        dates=get_text_from_cell(row, 8, get_link_text=True)
                    )

                    # Convert Course object to dict for state tracking
                    course_dict = {
                        'status': course.status,
                        'crn': course.crn,
                        'subject': course.subject,
                        'course_num': course.course_num,
                        'title': course.title,
                        'campus': course.campus,
                        'dates': course.dates,
                        'instructor': course.instructor
                    }

                    courses.append(course_dict)

                except Exception as e:
                    print(f"Error processing row: {str(e)}")
                    continue

            # Print parsed courses to console
            print("\nParsed Courses:")
            print("=" * 80)
            for course in courses:
                print(f"\n{course['subject']} {course['course_num']}: {course['title']}")
                print(f"CRN: {course['crn']}")
                print(f"Status: {course['status']}")
                print(f"Instructor: {course['instructor']}")
                print(f"Campus: {course['campus']}")
                print(f"Dates: {course['dates']}")
                print("-" * 80)

            # Convert list to dictionary with CRN as key for easier comparison
            return {course['crn']: course for course in courses}

        except Exception as e:
            print(f"Error during parsing: {str(e)}")
            return {}

    def close(self):
        """Close the browser"""
        self.driver.quit()