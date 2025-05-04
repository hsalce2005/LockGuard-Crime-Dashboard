from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import os
import requests
import camelot
import pandas as pd
'''
Script that scrapes webpage for reading in one PDf file. Used for:
- Arizona State University
- Boston University
- Cincinnati University
- Rutgers University
- University of Central Florida
- University of Minnesota
- University of South Carolina
- University of South California
- University of Pennsylvania
- University of Washington
- Wisconsin Madison
'''

# Chrome WebDriver
options = webdriver.ChromeOptions()
options.add_argument("--headless")
driver = webdriver.Chrome(options=options)

keywords = ['blotter']
url = "https://police.universitysafety.uconn.edu/uconn-crime-log/"
driver.get(url)

time.sleep(3)

pdf_links = driver.find_elements(By.XPATH, "//a[contains(@href, '.pdf')]")

# where to save the downloaded PDFs/CSVs
download_folder = "crimelog_pdfs"
csv_folder = "crimelog_csvs"
os.makedirs(download_folder, exist_ok=True)
os.makedirs(csv_folder, exist_ok=True)

def contains_keyword(pdf_url, keywords):
    return any(keyword.lower() in pdf_url.lower() for keyword in keywords)

for link in pdf_links:
    pdf_url = link.get_attribute('href')

    if contains_keyword(pdf_url, keywords):
        pdf_name = os.path.join(download_folder, pdf_url.split("/")[-1])

        response = requests.get(pdf_url)

        if response.status_code == 200:
            with open(pdf_name, 'wb') as pdf_file:
                pdf_file.write(response.content)
                print(f"Downloaded: {pdf_name}")

            try:
                tables = camelot.read_pdf(pdf_name, pages='1-end', flavor='stream')

                if tables:
                    combined_df = pd.DataFrame()

                    for table in tables:
                        combined_df = pd.concat([combined_df, table.df], ignore_index=True)

                    # save combined df to a single CSV file
                    csv_name = os.path.join(csv_folder, pdf_name.split("/")[-1].replace(".pdf", ".csv"))
                    combined_df.to_csv(csv_name, index=False)  # save without index
                    print(f"Converted to CSV: {csv_name}")

            except Exception as e:
                print(f"Error processing {pdf_name}: {e}")
        # debug
        else:
            print(f"Failed to download: {pdf_url}")
    else:
        print(f"Skipped (no keywords found): {pdf_url}")  # likely reports fire log

# Close the WebDriver
driver.quit()
