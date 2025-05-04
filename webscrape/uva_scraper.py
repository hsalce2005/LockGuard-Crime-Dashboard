from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import csv
import re
import time
import os


def setup_driver():
    """Set up and return a Selenium WebDriver"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode (no GUI)
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    # Use webdriver_manager to handle driver installation
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver


def parse_crime_log(driver, url):
    """Parse a monthly crime log page and extract incidents"""
    print(f"Scraping: {url}")
    driver.get(url)

    # Wait for page to load
    time.sleep(3)

    # Extract page title for month/year
    try:
        title = driver.find_element(By.TAG_NAME, "h1").text.strip()
    except:
        # If h1 not found, extract month/year from URL
        match = re.search(r'crime-log/([a-z]+-\d{4})', url, re.IGNORECASE)
        title = match.group(1).replace('-', ' ').title() if match else "Unknown Month"

    month_year = title
    print(f"Processing {month_year}")

    # Get page HTML for BeautifulSoup parsing
    page_source = driver.page_source
    soup = BeautifulSoup(page_source, 'html.parser')

    # Find all crime entries
    incidents = []

    # Based on your sample images, each crime entry has a pattern:
    # Incident type - Location     Case Number
    # Description text
    # RPT: time OCC: time to time
    # Case Status: status

    # Extract content from the page
    content = soup.get_text()

    # Split content into individual incident entries
    # This regex pattern looks for the pattern of uppercase incident types followed by locations
    incident_blocks = re.findall(
        r'([A-Z][A-Z\s/\-]+\s*-\s*[^\n]+\s+\d{10}/\d{2}[^\n]*(?:\n[^\n]+)*?Case Status:[^\n]+)', content, re.DOTALL)

    if not incident_blocks:
        print(f"Warning: No incident blocks found on {url}")
        # Print a sample of the content to debug
        print("Page content sample:")
        print(content[:500])

        # Try an alternative approach - look for specific patterns
        # Look for case numbers first as anchors
        case_numbers = re.findall(r'(\d{10}/\d{2})', content)
        print(f"Found {len(case_numbers)} case numbers")

        # If we found case numbers, try to extract incidents around them
        if case_numbers:
            for case_num in case_numbers:
                # Get text around the case number
                match_pos = content.find(case_num)
                if match_pos > 0:
                    # Extract 200 chars before and 500 chars after as a block
                    start_pos = max(0, match_pos - 200)
                    end_pos = min(len(content), match_pos + 500)
                    block = content[start_pos:end_pos]

                    # Now parse this block
                    incident_type_match = re.search(r'([A-Z][A-Z\s/\-]+)\s*-', block)
                    location_match = re.search(r'-\s*([^\n]+?)(?=\s+\d{10}/\d{2}|\s*$)', block)
                    description_match = re.search(r'Reported\s+(.*?)(?=\s*RPT:|$)', block, re.DOTALL)
                    report_time_match = re.search(r'RPT:\s*(\d{4}\s+\d{2}-\d{2}-\d{4})', block)
                    occurrence_time_match = re.search(r'OCC:\s*(.*?)(?=\s+to\s+|$)', block)
                    occurrence_end_match = re.search(r'to\s+(\d{4}\s+\d{2}-\d{2}-\d{4})', block)
                    case_status_match = re.search(r'Case Status:\s*(.*?)(?=$|\n)', block)

                    incident = {
                        'Month_Year': month_year,
                        'Incident_Type': incident_type_match.group(1).strip() if incident_type_match else '',
                        'Location': location_match.group(1).strip() if location_match else '',
                        'Case_Number': case_num,
                        'Description': description_match.group(1).strip() if description_match else '',
                        'Report_Time': report_time_match.group(1).strip() if report_time_match else '',
                        'Occurrence_Time': occurrence_time_match.group(1).strip() if occurrence_time_match else '',
                        'Occurrence_End': occurrence_end_match.group(1).strip() if occurrence_end_match else '',
                        'Case_Status': case_status_match.group(1).strip() if case_status_match else ''
                    }
                    incidents.append(incident)
    else:
        for block in incident_blocks:
            # Extract information using regex patterns based on your example images
            incident_type_match = re.search(r'^([A-Z][A-Z\s/\-]+)\s*-', block)
            location_match = re.search(r'-\s*([^\n]+?)(?=\s+\d{10}/\d{2})', block)
            case_number_match = re.search(r'(\d{10}/\d{2})', block)
            description_match = re.search(r'Reported\s+(.*?)(?=\s*RPT:|$)', block, re.DOTALL)
            report_time_match = re.search(r'RPT:\s*(\d{4}\s+\d{2}-\d{2}-\d{4})', block)
            occurrence_time_match = re.search(r'OCC:\s*(.*?)(?=\s+to\s+|$)', block)
            occurrence_end_match = re.search(r'to\s+(\d{4}\s+\d{2}-\d{2}-\d{4})', block)
            case_status_match = re.search(r'Case Status:\s*(.*?)$', block, re.MULTILINE)

            incident = {
                'Month_Year': month_year,
                'Incident_Type': incident_type_match.group(1).strip() if incident_type_match else '',
                'Location': location_match.group(1).strip() if location_match else '',
                'Case_Number': case_number_match.group(1).strip() if case_number_match else '',
                'Description': description_match.group(1).strip() if description_match else '',
                'Report_Time': report_time_match.group(1).strip() if report_time_match else '',
                'Occurrence_Time': occurrence_time_match.group(1).strip() if occurrence_time_match else '',
                'Occurrence_End': occurrence_end_match.group(1).strip() if occurrence_end_match else '',
                'Case_Status': case_status_match.group(1).strip() if case_status_match else ''
            }
            incidents.append(incident)

    print(f"Extracted {len(incidents)} incidents from {url}")
    return incidents


def save_to_csv(incidents, filename='uva_crime_log.csv'):
    """Save incidents to a CSV file"""
    # Check if file exists to write headers only once
    file_exists = os.path.isfile(filename)

    with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            'Month_Year', 'Incident_Type', 'Location', 'Case_Number',
            'Description', 'Report_Time', 'Occurrence_Time', 'Occurrence_End', 'Case_Status'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        for incident in incidents:
            writer.writerow(incident)

    print(f"Data saved to {filename}")


def main():
    output_file = 'uva_crime_log.csv'

    # Define specific URLs to scrape
    monthly_urls = [
        "https://uvapolice.virginia.edu/crime-log/march-2025",
        "https://uvapolice.virginia.edu/crime-log/february-2025",
        "https://uvapolice.virginia.edu/crime-log/january-2025",
        "https://uvapolice.virginia.edu/crime-log/april-2025"
    ]

    # Set up Selenium WebDriver
    driver = setup_driver()

    try:
        # Create a new CSV file (overwrite if exists)
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'Month_Year', 'Incident_Type', 'Location', 'Case_Number',
                'Description', 'Report_Time', 'Occurrence_Time', 'Occurrence_End', 'Case_Status'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

        # Process each monthly page
        all_incidents = []
        for url in monthly_urls:
            incidents = parse_crime_log(driver, url)
            all_incidents.extend(incidents)

            # Add a short delay to avoid overloading the server
            time.sleep(2)

        # Save all incidents to CSV
        save_to_csv(all_incidents, output_file)
        print(f"Scraping complete. Total incidents: {len(all_incidents)}")

    finally:
        # Always close the driver
        driver.quit()


if __name__ == "__main__":
    main()