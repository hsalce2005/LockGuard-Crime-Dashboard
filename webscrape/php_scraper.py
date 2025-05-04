import requests
from bs4 import BeautifulSoup
import csv
import os
import time
import re
from datetime import datetime
import pandas as pd

'''
Script to scrape webpages ending with '.php'. Used for:
- Purdue University
'''


def scrape_crime_logs():
    # Base URL
    base_url = "https://sc.edu/about/offices_and_divisions/law_enforcement_and_safety/crime-log-bulletins/"

    # Get the main index page
    main_page_url = base_url + "index.php"
    main_response = requests.get(main_page_url)
    main_soup = BeautifulSoup(main_response.text, 'html.parser')

    # Find all weekly log links
    weekly_links = []
    for link in main_soup.find_all('a'):
        href = link.get('href')
        if href and "Week of" in link.text:
            if href.startswith('http'):
                weekly_links.append(href)
            else:
                weekly_links.append(base_url + href)

    # Create CSV file to store all data
    csv_filename = "purdue_crime_logs.csv"

    # CSV headers
    headers = ["Date", "Nature", "Case Number", "Date/Time Occurred",
               "Date/Time Reported", "General Location", "Disposition"]

    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(headers)

        # Process each weekly link
        for weekly_url in weekly_links:
            print(f"Processing: {weekly_url}")

            try:
                weekly_response = requests.get(weekly_url)
                weekly_soup = BeautifulSoup(weekly_response.text, 'html.parser')

                # Find all daily log tables
                current_date = None

                # Identify dates first (they're typically h2 or h3 elements)
                date_headers = weekly_soup.find_all(['h2', 'h3'])

                for header in date_headers:
                    if re.search(
                            r'\b(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),\s+\w+\s+\d+,\s+\d{4}\b',
                            header.text):
                        current_date = header.text.strip()
                        print(f"  Found date: {current_date}")

                        # Find the next table after this date header
                        table = header.find_next('table')

                        if table:
                            # Extract rows from the table
                            rows = table.find_all('tr')

                            # Skip header row
                            for row in rows[1:]:
                                cells = row.find_all(['td', 'th'])
                                if len(cells) >= 6:  # Ensure we have enough cells
                                    # Extract data from cells
                                    nature = cells[0].text.strip()
                                    case_number = cells[1].text.strip()
                                    date_time_occurred = cells[2].text.strip()
                                    date_time_reported = cells[3].text.strip()
                                    location = cells[4].text.strip()
                                    disposition = cells[5].text.strip()

                                    # Write to CSV
                                    writer.writerow([
                                        current_date,
                                        nature,
                                        case_number,
                                        date_time_occurred,
                                        date_time_reported,
                                        location,
                                        disposition
                                    ])

                # Wait between requests to avoid overloading the server
                time.sleep(1)

            except Exception as e:
                print(f"Error processing {weekly_url}: {e}")

    print(f"Data saved to {csv_filename}")

    # Convert CSV to a more readable DataFrame
    df = pd.read_csv(csv_filename)
    print(f"Total records collected: {len(df)}")
    return df


if __name__ == "__main__":
    crime_data = scrape_crime_logs()