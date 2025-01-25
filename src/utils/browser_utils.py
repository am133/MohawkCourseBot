from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

def initialize_driver():
    """Initialize and configure the Chrome WebDriver."""
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')

    driver = webdriver.Chrome(options=chrome_options)
    wait = WebDriverWait(driver, 120)  # 120 second timeout
    return driver, wait


def get_text_from_cell(row, cell_index, get_link_text=False):
    """Extract text from a cell, optionally getting link text."""
    try:
        if get_link_text:
            return row.find_element(By.XPATH, f"./td[{cell_index}]//a").text.strip()
        return row.find_element(By.XPATH, f"./td[{cell_index}]").text.strip()
    except NoSuchElementException:
        return ""


def determine_status(row):
    """Determine the status of a course (Registered, Full, or Available)."""
    checkbox = row.find_elements(By.XPATH, ".//input[@type='checkbox']")
    if checkbox:
        checkbox_value = checkbox[0].get_attribute("value")
        if checkbox_value and "Registered" in checkbox_value:
            return "Registered"
        if checkbox[0].get_attribute("checked") == "true":
            return "Registered"

    raw_status = get_text_from_cell(row, 2, get_link_text=True)
    if "Registered" in raw_status:
        return "Registered"
    elif "Full" in raw_status:
        return "Full"
    return "Available"
