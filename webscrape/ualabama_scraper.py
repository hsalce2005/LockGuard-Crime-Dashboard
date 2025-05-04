import requests
from bs4 import BeautifulSoup
import csv
import re
import logging
import time
from urllib.parse import urljoin

# Set up logging - only to console, no file
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)


def format_date_time(date_time_str):
    """
    Format date/time string from various formats to a standardized format
    """
    if not date_time_str or date_time_str.strip() == "":
        return ""

    try:
        # First, let's make the string lowercase for case-insensitive matching
        lower_str = date_time_str.lower()

        # If the string contains 'hrs', process it
        if 'hrs' in lower_str:
            # Format 1: Handle date with extra slash like "3/26/25/1028 Hrs"
            pattern1 = r'(\d+/\d+/\d+)/(\d{1,4})\s*hrs'
            match = re.match(pattern1, lower_str, re.IGNORECASE)

            if match:
                date_part = match.group(1)  # e.g., "3/26/25"
                time_part = match.group(2)  # e.g., "1028"

                # Format the time part to have a colon
                time_part = time_part.zfill(4)
                formatted_time = f"{time_part[:2]}:{time_part[2:]}"

                # Return the formatted date and time
                return f"{date_part} {formatted_time}"

            # Format 2: Standard format like "4/29/25 1217 Hrs"
            pattern2 = r'(\d+/\d+/\d+)\s+(\d{1,4})\s*hrs'
            match = re.match(pattern2, lower_str, re.IGNORECASE)

            if match:
                date_part = match.group(1)  # e.g., "4/29/25"
                time_part = match.group(2)  # e.g., "1217" or "945" or "1500"

                # Format the time part to have a colon
                time_part = time_part.zfill(4)
                formatted_time = f"{time_part[:2]}:{time_part[2:]}"

                # Return the formatted date and time
                return f"{date_part} {formatted_time}"

        # If we get here, the pattern didn't match or there was no 'hrs'
        # Return the original string
        return date_time_str
    except Exception as e:
        logging.warning(f"Error formatting date/time '{date_time_str}': {e}")
        return date_time_str


def scrape_crime_log_page(url):
    """
    Scrape a single page of the crime log
    """
    logging.info(f"Fetching data from {url}")

    # Send a request to the webpage
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for 4XX/5XX responses
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching the webpage: {e}")
        return None, None

    # Parse the HTML content
    soup = BeautifulSoup(response.content, 'html.parser')

    # The crime log is in an HTML table, but with a specific structure
    page_crime_data = []

    # Find the crime log table - it might be in various structures
    table = soup.find('table')
    if not table:
        logging.warning("No table found on the page. The structure might have changed.")
        return None, None

    # Find all rows in the table (might be direct or within a tbody)
    rows = table.find_all('tr')
    if not rows:
        logging.warning("No table rows found. The page structure might have changed.")
        return None, None

    logging.info(f"Found {len(rows)} potential table rows.")

    # Extract header row to get the column names (if present)
    headers = []
    if rows and rows[0].find_all('th'):
        header_row = rows[0]
        headers = [th.text.strip() for th in header_row.find_all('th')]
        rows = rows[1:]  # Skip the header row for data extraction

    # Process each row to extract crime data
    for row in rows:
        # Skip rows that don't contain crime data (might be empty or header rows)
        cells = row.find_all('td')
        if not cells or len(cells) < 5:  # Ensure we have enough cells for basic crime data
            continue

        # The data extraction needs to be adapted based on the actual structure of the page
        try:
            # Extract the report number (which might be in an <a> tag)
            report_cell = cells[0]
            report_link = report_cell.find('a')
            if report_link:
                report_number = report_link.text.strip()
                report_url = report_link.get('href', '')
            else:
                report_number = report_cell.text.strip()
                report_url = ''

            # Ensure this is an actual report number row and not some other content
            if not re.match(r'^R\d+', report_number):
                continue

            # Extract remaining data based on the structure observed
            # Note: Index positions are based on the observed structure in the source
            crime_type = cells[1].text.strip() if len(cells) > 1 else ""
            date_reported = cells[2].text.strip() if len(cells) > 2 else ""
            date_from = cells[3].text.strip() if len(cells) > 3 else ""
            date_to = cells[4].text.strip() if len(cells) > 4 else ""
            location = cells[5].text.strip() if len(cells) > 5 else ""
            status = cells[6].text.strip() if len(cells) > 6 else ""
            disposition_change = cells[7].text.strip() if len(cells) > 7 else ""
            disposition = cells[8].text.strip() if len(cells) > 8 else ""
            date_entered = cells[9].text.strip() if len(cells) > 9 else ""

            # Format the date/time fields
            date_reported_formatted = format_date_time(date_reported)
            date_from_formatted = format_date_time(date_from)
            date_to_formatted = format_date_time(date_to)

            # Create a dictionary for this crime entry
            entry = {
                'Report Number': report_number,
                'Report URL': report_url,
                'Crime Type': crime_type,
                'Date Reported': date_reported_formatted,
                'Date From': date_from_formatted,
                'Date To': date_to_formatted,
                'Location': location,
                'Status': status,
                'Disposition Change': disposition_change,
                'Disposition': disposition,
                'Date Entered': date_entered
            }

            page_crime_data.append(entry)

        except Exception as e:
            logging.error(f"Error processing row: {e}")
            continue

    # Look for pagination links
    next_page_url = None
    pagination = soup.find('div', class_='dataTables_paginate')

    if pagination:
        # Look for the "Next" button or the next page number
        next_link = None

        # Try to find the next page link using various selectors
        # Option 1: Look for a "next" class
        next_link = pagination.find('a', class_='next')

        # Option 2: Look for a "›" symbol
        if not next_link:
            next_link = pagination.find('a', text='›')

        # Option 3: Look for the currently active page and get the next one
        if not next_link:
            current_page_element = pagination.find('a', class_='current')
            if current_page_element:
                current_page = int(current_page_element.text.strip())
                next_page_element = pagination.find('a', text=str(current_page + 1))
                if next_page_element:
                    next_link = next_page_element

        # If we found a next link, get its URL
        if next_link and 'disabled' not in next_link.get('class', []):
            next_href = next_link.get('href')
            if next_href:
                next_page_url = urljoin(url, next_href)

    logging.info(f"Extracted {len(page_crime_data)} crime log entries from this page.")
    return page_crime_data, next_page_url


def scrape_all_pages():
    """
    Scrape all pages of the crime log
    """
    base_url = "https://police.ua.edu/daily-crime-log/"
    current_url = base_url
    all_crime_data = []
    page_num = 1

    while current_url:
        logging.info(f"Scraping page {page_num}...")
        page_data, next_url = scrape_crime_log_page(current_url)

        if page_data:
            all_crime_data.extend(page_data)
            logging.info(f"Cumulative entries: {len(all_crime_data)}")
        else:
            logging.warning(f"No data found on page {page_num}. Stopping.")
            break

        # If there's a next page, update the URL for the next iteration
        if next_url:
            current_url = next_url
            page_num += 1
            # Add a small delay to avoid overwhelming the server
            time.sleep(1)
        else:
            logging.info("No more pages to scrape.")
            break

    return all_crime_data


def save_to_csv(crime_data, filename="UniversityOfArizona.csv"):
    """Save the crime log data to a CSV file"""
    if not crime_data:
        logging.error("No data to save to CSV.")
        return False

    # Define the field names for the CSV
    fieldnames = [
        'Report Number', 'Report URL', 'Crime Type', 'Date Reported',
        'Date From', 'Date To', 'Location', 'Status',
        'Disposition Change', 'Disposition', 'Date Entered'
    ]

    try:
        # Write data to CSV file
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            # Write header
            writer.writeheader()

            # Write data rows
            writer.writerows(crime_data)

        logging.info(f"Successfully saved {len(crime_data)} entries to {filename}")
        return True
    except Exception as e:
        logging.error(f"Error saving to CSV: {e}")
        return False


def main():
    logging.info("Starting UA Police Department Crime Log Scraper")

    # Scrape all pages of the crime log
    crime_data = scrape_all_pages()

    if crime_data:
        # Save to CSV
        success = save_to_csv(crime_data)
        if success:
            logging.info("Scraping completed successfully!")
        else:
            logging.error("Failed to save scraped data to CSV.")
    else:
        logging.error("Failed to scrape crime log data.")


if __name__ == "__main__":
    main()