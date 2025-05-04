from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import os
import requests
import camelot
import pandas as pd

'''
Script to scrape websites where there are multiple PDF files to scrape. Used for:
- FIU
- UConn
- UC Berkeley
- Virginia Tech
'''


# Chrome WebDriver
options = webdriver.ChromeOptions()
options.add_argument("--headless")
driver = webdriver.Chrome(options=options)

# keywords to specifically select crime log links
keywords = ['blotter']

url = "https://police.universitysafety.uconn.edu/uconn-crime-log/"
driver.get(url)
time.sleep(3)

pdf_links = driver.find_elements(By.XPATH, "//a[contains(@href, '.pdf')]")

download_folder = "crimelog_pdfs"
os.makedirs(download_folder, exist_ok=True)



all_tables = []

# making sure keywords are in PDF links
def contains_keyword(pdf_url, keywords):
    return any(keyword.lower() in pdf_url.lower() for keyword in keywords)


def scrape_pdf_to_df(pdf_url):
    # downloads PDF
    pdf_name = os.path.join(download_folder, pdf_url.split("/")[-1])
    response = requests.get(pdf_url)

    if response.status_code == 200:
        with open(pdf_name, 'wb') as pdf_file:
            pdf_file.write(response.content)
            print(f"Downloaded: {pdf_name}")

        try:
            tables = camelot.read_pdf(pdf_name, pages='1-end', flavor='stream')

            if tables:
                for table in tables:
                    all_tables.append(table.df)

        except Exception as e:
            print(f"Error processing {pdf_name}: {e}")
    else:
        print(f"Failed to download: {pdf_url}")


# iterate through each link and process the PDFs
for link in pdf_links:
    pdf_url = link.get_attribute('href')

    if contains_keyword(pdf_url, keywords):
        print(f"Processing: {pdf_url}")
        scrape_pdf_to_df(pdf_url)
    else:
        print(f"Skipped (no keywords found): {pdf_url}")

combined_df = pd.concat(all_tables, ignore_index=True)

excel_file = "../clean/crimelog_data.xlsx"
combined_df.to_excel(excel_file, index=False)

# Close the WebDriver
driver.quit()
