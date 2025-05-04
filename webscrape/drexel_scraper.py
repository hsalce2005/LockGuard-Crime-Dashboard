import requests
import pdfplumber
import pandas as pd
import re
import os
from datetime import datetime


def download_pdf(url, save_path):
    """Download the PDF file from the given URL and save it to the specified path."""
    try:
        response = requests.get(url)
        if response.status_code == 200:
            with open(save_path, 'wb') as f:
                f.write(response.content)
            print(f"PDF downloaded and saved to {save_path}")
            return True
        else:
            print(f"Failed to download PDF. Status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"Error downloading PDF: {e}")
        return False


def extract_text_from_pdf(pdf_path):
    """Extract text from PDF file using pdfplumber"""
    full_text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                print(f"Extracting text from page {page.page_number} of {len(pdf.pages)}")
                page_text = page.extract_text()
                if page_text:
                    full_text += page_text + "\n"
        return full_text
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return ""


def parse_drexel_crime_log(text):
    """Parse the Drexel crime log format using the specific patterns"""
    incidents = []

    # Extract all date reported sections with report numbers
    # This complex pattern looks for Date Reported sections followed by all data up to next Date Reported
    sections = re.split(r'(Date Reported:[^\n]+)', text)

    print(f"Found {len(sections)} sections in the document")

    # Process the sections
    current_date_reported = None
    current_section = ""

    for section in sections:
        if section.strip().startswith("Date Reported:"):
            # This is a header section
            current_date_reported = section.strip()
            current_section = current_date_reported
        elif current_date_reported is not None:
            # This is a content section
            current_section += "\n" + section

            # Extract Report Number
            report_match = re.search(r'Report #:\s*(\d+-\d+)', current_section)
            if not report_match:
                continue

            report_num = report_match.group(1).strip()

            # Extract Date/Time Reported - just first date and time
            date_reported_match = re.search(r'Date Reported:\s+([\d/]+)\s+-\s+\w+\s+at\s+([\d:]+)', current_section)
            date_reported = ""
            if date_reported_match:
                date_reported = f"{date_reported_match.group(1)} {date_reported_match.group(2)}"

            # Extract Location
            location_match = re.search(r'Location\s*:\s*([^\n]+)', current_section)
            location = location_match.group(1).strip() if location_match else ""

            # Extract Incident Type
            incident_match = re.search(r'Incident\(s\):\s*([^\n]+)', current_section)
            incident_type = ""
            if incident_match:
                incident_type = incident_match.group(1).strip()
                # Convert to proper case (Title case)
                incident_type = incident_type.title()

            # Extract Date/Time Occurred - just first date and time
            occurred_match = re.search(
                r'Date and Time Occurred From - Occurred To:\s+([\d/]+)\s+-\s+\w+\s+at\s+([\d:]+)', current_section)
            date_occurred = ""
            if occurred_match:
                date_occurred = f"{occurred_match.group(1)} {occurred_match.group(2)}"

            # Extract Disposition
            disp_match = re.search(r'Disposition:\s*([^\n]+)', current_section)
            disposition = ""
            if disp_match:
                disposition = disp_match.group(1).strip()
                # Convert to proper case (Title case)
                disposition = disposition.title()

            # Only add if we have the minimum data
            if report_num:
                incident = {
                    'Case Number': report_num,
                    'Date/Time Reported': date_reported,
                    'Date/Time Occurred': date_occurred,
                    'Report #': report_num,
                    'Location': location,
                    'Incident Type': incident_type,
                    'Disposition': disposition
                }
                incidents.append(incident)
                print(f"Added incident: {report_num}")

            # Reset for next section
            current_date_reported = None
            current_section = ""

    # If the above method fails, try an alternative approach
    if not incidents:
        print("First method didn't find incidents, trying alternative approach...")

        # Look for all report numbers in the document
        report_matches = list(re.finditer(r'Report #:\s*(\d+-\d+)', text))
        print(f"Found {len(report_matches)} report numbers")

        for i, match in enumerate(report_matches):
            report_num = match.group(1)

            # Extract a section of text around this report number (approx. ±30 lines)
            start_pos = max(0, match.start() - 1500)  # Go back roughly 1500 chars
            end_pos = min(len(text), match.end() + 1500)  # Go forward roughly 1500 chars

            section = text[start_pos:end_pos]

            # Extract Date/Time Reported - just first date and time
            date_reported_match = re.search(r'Date Reported:\s+([\d/]+)\s+-\s+\w+\s+at\s+([\d:]+)', section)
            date_reported = ""
            if date_reported_match:
                date_reported = f"{date_reported_match.group(1)} {date_reported_match.group(2)}"

            # Extract Location
            location_match = re.search(r'Location\s*:\s*([^\n]+)', section)
            location = location_match.group(1).strip() if location_match else ""

            # Extract Incident Type
            incident_match = re.search(r'Incident\(s\):\s*([^\n]+)', section)
            incident_type = ""
            if incident_match:
                incident_type = incident_match.group(1).strip()
                # Convert to proper case (Title case)
                incident_type = incident_type.title()

            # Extract Date/Time Occurred - just first date and time
            occurred_match = re.search(
                r'Date and Time Occurred From - Occurred To:\s+([\d/]+)\s+-\s+\w+\s+at\s+([\d:]+)', section)
            date_occurred = ""
            if occurred_match:
                date_occurred = f"{occurred_match.group(1)} {occurred_match.group(2)}"

            # Extract Disposition
            disp_match = re.search(r'Disposition:\s*([^\n]+)', section)
            disposition = ""
            if disp_match:
                disposition = disp_match.group(1).strip()
                # Convert to proper case (Title case)
                disposition = disposition.title()

            # Create incident record
            incident = {
                'Case Number': report_num,
                'Date/Time Reported': date_reported,
                'Date/Time Occurred': date_occurred,
                'Report #': report_num,
                'Location': location,
                'Incident Type': incident_type,
                'Disposition': disposition
            }

            incidents.append(incident)
            print(f"Added incident using method 2: {report_num}")

    print(f"Successfully parsed {len(incidents)} incidents")
    return incidents


def write_to_csv(incidents, output_path):
    """Write incidents to CSV file"""
    if not incidents:
        print("No incidents to write.")
        return False

    try:
        fieldnames = [
            'Case Number', 'Date/Time Reported', 'Date/Time Occurred',
            'Report #', 'Location', 'Incident Type', 'Disposition'
        ]

        df = pd.DataFrame(incidents)

        # Ensure all required columns are present
        for col in fieldnames:
            if col not in df.columns:
                df[col] = ""

        # Select and order columns
        df = df[fieldnames]

        # Save to CSV
        df.to_csv(output_path, index=False)
        print(f"Successfully wrote {len(incidents)} incidents to {output_path}")
        return True

    except Exception as e:
        print(f"Error writing to CSV: {e}")
        return False


def main():
    url = "https://drexel.edu/~/media/Files/publicsafety/PDF/DrexelDailyCrimeLog.ashx?la=en"
    pdf_path = "DrexelDailyCrimeLog.pdf"
    output_csv = "output.csv"

    print(f"Downloading PDF from {url}...")
    if not download_pdf(url, pdf_path):
        print("Failed to download PDF. Exiting.")
        return

    print(f"Extracting text from {pdf_path}...")
    text = extract_text_from_pdf(pdf_path)
    if not text:
        print("Failed to extract text from PDF. Exiting.")
        return

    # Save extracted text for debugging (optional)
    with open("extracted_text.txt", "w", encoding="utf-8") as f:
        f.write(text)

    print("Parsing crime log...")
    incidents = parse_drexel_crime_log(text)

    print(f"Writing to CSV: {output_csv}")
    write_to_csv(incidents, output_csv)

    print("Done!")


if __name__ == "__main__":
    main()