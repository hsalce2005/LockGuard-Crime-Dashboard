from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import csv
import time

'''
Script for navigating multiple pages with tables. Used for
- Penn State
- University of Arizona
- UChicago
'''


# Chrome WebDriver
driver = webdriver.Chrome()
driver.get("https://incidentreports.uchicago.edu/incidentReportArchive.php?startDate=01%2F01%2F2025&endDate=05%2F01%2F2025")
wait = WebDriverWait(driver, 10)

table_data = []
headers = None

def extract_table_data():
    """Extracts data from the table on the current page."""
    global headers

    try:
        table = wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
    except:
        return False

    if headers is None:
        headers = [th.text.strip() for th in table.find_elements(By.TAG_NAME, "th")]

    rows = table.find_elements(By.TAG_NAME, "tr")[1:]  # Skip header row
    for row in rows:
        cells = row.find_elements(By.TAG_NAME, "td")
        table_data.append([cell.text.strip() for cell in cells])

    return True

max_pages = 500
page_number = 5

while page_number <= max_pages:
    driver.get(f"https://incidentreports.uchicago.edu/incidentReportArchive.php?startDate=1735711200&endDate=1746075600&offset={page_number}")
    time.sleep(3)

    if not extract_table_data():
        break

    print(f"Scraped page {page_number}")
    page_number += 5

csv_filename = "crime_log.csv"
with open(csv_filename, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(headers)
    writer.writerows(table_data)

print(f"✅ Data exported successfully to {csv_filename}")

# Close browser
driver.quit()
