import requests
import pandas as pd
import PyPDF2
import io
import re
from bs4 import BeautifulSoup
import time
from datetime import datetime, timedelta


def scrape_ucsd_police_logs():
    """
    Scrape UCSD Police Department crime logs from their website.
    Extract data from PDF files for each date and compile into a CSV.
    Focus on March 3 - March 26, 2025 date range.
    """
    # Base URL for the UCSD Police Department website
    base_url = "https://www.police.ucsd.edu/docs/reports/callsandarrests/"

    # Create a session for making HTTP requests
    session = requests.Session()

    # Define the specific date range we want (March 3 - March 26, 2025)
    start_date = datetime(2025, 3, 3)
    end_date = datetime(2025, 3, 26)

    # Generate the dates in the range
    dates_to_process = []
    current_date = start_date

    while current_date <= end_date:
        month_name = current_date.strftime("%B")
        day = current_date.day
        year = current_date.year
        date_str = f"{month_name} {day}, {year}"
        dates_to_process.append(date_str)
        current_date += timedelta(days=1)

    print(
        f"Will process {len(dates_to_process)} dates from {start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')}")

    # Initialize a list to store all incident data
    all_incidents = []
    processed_count = 0

    for date_str in dates_to_process:
        try:
            # Format the date for the PDF URL
            parts = date_str.split()
            month = parts[0]  # e.g., "March"
            day_with_comma = parts[1]  # e.g., "9,"
            year = parts[2]  # e.g., "2025"

            # URL encode the date
            encoded_date = f"{month}%20{day_with_comma}%20{year}"
            pdf_url = f"{base_url}CallsForService/{encoded_date}.pdf"

            print(f"Trying URL: {pdf_url}")

            # Get the PDF
            pdf_response = session.get(pdf_url)

            if pdf_response.status_code == 200:
                # Process the PDF and extract incidents
                incidents = extract_incidents_pdf_direct(pdf_response.content, date_str)
                if incidents:
                    all_incidents.extend(incidents)
                    processed_count += 1
                    print(f"Successfully extracted {len(incidents)} incidents from {date_str}")
                else:
                    print(f"No incidents found in {date_str}")
            else:
                print(f"Failed to get PDF for {date_str}: Status code {pdf_response.status_code}")

            # Add a short delay to avoid overwhelming the server
            time.sleep(0.5)

        except Exception as e:
            print(f"Error processing {date_str}: {str(e)}")

    print(f"Successfully processed {processed_count} out of {len(dates_to_process)} dates")

    # Create a DataFrame and save to CSV if we have data
    if all_incidents:
        df = pd.DataFrame(all_incidents)

        # Ensure the DataFrame has all expected columns
        expected_columns = [
            'Report_Date', 'Case_Number', 'Incident_Type', 'Location',
            'Date_Reported', 'Date_Occurred', 'Time_Occurred',
            'Summary', 'Disposition'
        ]

        for col in expected_columns:
            if col not in df.columns:
                df[col] = ""

        # Reorder columns
        df = df[expected_columns]

        # Save to CSV
        output_file = "ucsd_police_logs.csv"
        df.to_csv(output_file, index=False)
        print(f"Data saved to {output_file} with {len(all_incidents)} total incidents")
        return df
    else:
        print("No data collected")
        return None


def extract_incidents_pdf_direct(pdf_content, date_string):
    """
    Extract incidents directly from the PDF with focus on incident type and location.

    This approach directly extracts the raw PDF text and then analyzes its layout
    to identify incident type and location patterns.

    Args:
        pdf_content: The binary content of the PDF
        date_string: The date string for this report

    Returns:
        A list of dictionaries, each containing information about one incident
    """
    incidents = []
    try:
        # Create a PDF reader object
        pdf_file = io.BytesIO(pdf_content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)

        # First, extract all text while preserving page structure
        all_pages_text = []
        for page in range(len(pdf_reader.pages)):
            page_text = pdf_reader.pages[page].extract_text()
            all_pages_text.append(page_text)

        # Now extract blocks of incident data from each page
        for page_text in all_pages_text:
            # First, find all the case numbers on this page
            case_matches = list(re.finditer(r'Incident/Case#\s+([\w\d-]+)', page_text))

            for i, case_match in enumerate(case_matches):
                try:
                    case_number = case_match.group(1).strip()
                    case_start = case_match.start()

                    # Determine the end of this incident block (start of next case or end of page)
                    case_end = len(page_text)
                    if i < len(case_matches) - 1:
                        case_end = case_matches[i + 1].start()

                    # Extract the block of text for this incident
                    incident_block = page_text[case_start:case_end]

                    # Extract the structured data using regex
                    date_reported = extract_value(incident_block, r'Date Reported\s+([\d/]+)')
                    date_occurred = extract_value(incident_block, r'Date Occurred\s+([\d/]+(?:\s*-\s*[\d/]+)?)')
                    time_occurred = extract_value(incident_block,
                                                  r'Time Occurred\s+([\d:]+\s*(?:AM|PM)(?:\s*-\s*[\d:]+\s*(?:AM|PM))?)')

                    # Find the summary and disposition
                    summary_match = re.search(r'Summary:\s+(.*?)(?=Disposition:|$)', incident_block, re.DOTALL)
                    summary = summary_match.group(1).strip() if summary_match else ""

                    disposition_match = re.search(r'Disposition:\s+(.*?)(?=Date Reported|\Z)', incident_block,
                                                  re.DOTALL)
                    disposition = ""
                    if disposition_match:
                        disp_text = disposition_match.group(1).strip()
                        # The disposition is the first line after "Disposition:"
                        disp_lines = disp_text.split('\n')
                        disposition = disp_lines[0].strip() if disp_lines else ""

                        # Now the crucial part - extract incident type and location
                        # They appear after the disposition (lines 2 and 3)
                        if len(disp_lines) > 1:
                            # Line 2 is typically the incident type
                            incident_type = disp_lines[1].strip()
                            # Line 3 is typically the location
                            location = disp_lines[2].strip() if len(disp_lines) > 2 else ""

                            # If the incident type or location contains structural text, discard it
                            if "Date Reported" in incident_type or "Incident/Case#" in incident_type:
                                incident_type = ""
                            if "Date Reported" in location or "Incident/Case#" in location:
                                location = ""

                            # Clean up the incident type and location
                            incident_type = clean_text(incident_type)
                            location = clean_text(location)

                            # Add to our list if we have enough data
                            incidents.append({
                                'Report_Date': date_string,
                                'Case_Number': case_number,
                                'Incident_Type': incident_type,
                                'Location': location,
                                'Date_Reported': date_reported,
                                'Date_Occurred': date_occurred,
                                'Time_Occurred': time_occurred,
                                'Summary': summary,
                                'Disposition': disposition
                            })
                        else:
                            # If we don't have lines after disposition, try to find patterns in the text
                            # Look for common incident types and the text that follows them
                            # This is a fallback method
                            incident_type = ""
                            location = ""

                            # Create a temporary incident record without type/location
                            incidents.append({
                                'Report_Date': date_string,
                                'Case_Number': case_number,
                                'Incident_Type': incident_type,
                                'Location': location,
                                'Date_Reported': date_reported,
                                'Date_Occurred': date_occurred,
                                'Time_Occurred': time_occurred,
                                'Summary': summary,
                                'Disposition': disposition
                            })
                    else:
                        # If we can't find a disposition, just add the basic data
                        incidents.append({
                            'Report_Date': date_string,
                            'Case_Number': case_number,
                            'Incident_Type': "",
                            'Location': "",
                            'Date_Reported': date_reported,
                            'Date_Occurred': date_occurred,
                            'Time_Occurred': time_occurred,
                            'Summary': summary,
                            'Disposition': ""
                        })

                except Exception as e:
                    print(f"Error processing case {case_number} in {date_string}: {str(e)}")

        # Second pass: For each incident with empty incident_type and location,
        # look at the raw text of the PDF and try to find these values
        if incidents:
            # First, create a combined text of all pages for easier searching
            full_text = "\n".join(all_pages_text)

            # For each incident that's missing type/location
            for i, incident in enumerate(incidents):
                if not incident['Incident_Type'] or not incident['Location']:
                    case_number = incident['Case_Number']

                    # Look for common patterns where incident type and location appear together
                    # For example: "Medical Aid\nLocation name\n"
                    common_types = [
                        "Medical Aid", "Welfare Check", "Petty Theft", "Grand Theft",
                        "Fire Alarm", "Security Alarm", "Noise Disturbance", "Suspicious Person",
                        "Traffic", "Burglary", "Vandalism", "Trespass", "Drunk Driving",
                        "Mental Health", "Elevator Problem", "Animal Call", "Information",
                        "Escort", "Citizen Contact", "Simple Assault", "Hit and Run",
                        "Drug Law", "Shoplifting", "Suspicious Circumstances", "UC Policy Violation"
                    ]

                    # Find where this case number appears in the full text
                    case_pos = full_text.find(f"Incident/Case# {case_number}")

                    if case_pos >= 0:
                        # Look at the text following this case number
                        following_text = full_text[case_pos:case_pos + 1000]  # Look at the next 1000 chars

                        # Try to identify incident type and location by looking for patterns
                        for type_str in common_types:
                            type_pos = following_text.find(type_str)
                            if type_pos >= 0:
                                # Found a potential incident type
                                type_end = type_pos + len(type_str)

                                # The location is typically the next line after the incident type
                                loc_start = following_text.find('\n', type_end)
                                if loc_start >= 0:
                                    loc_start += 1  # Skip the newline
                                    loc_end = following_text.find('\n', loc_start)
                                    if loc_end >= 0:
                                        location = following_text[loc_start:loc_end].strip()

                                        # Update the incident
                                        incident['Incident_Type'] = type_str
                                        incident['Location'] = clean_text(location)
                                        break

                    # If still no incident type, try looking for it in the disposition
                    if not incident['Incident_Type'] and incident['Disposition']:
                        for type_str in common_types:
                            if type_str in incident['Disposition']:
                                incident['Incident_Type'] = type_str
                                break

    except Exception as e:
        print(f"Error processing PDF for {date_string}: {str(e)}")

    return incidents


def clean_text(text):
    """Clean up text to remove headers and structural text"""
    if not text:
        return ""

    # Remove headers
    text = text.replace("UCSD POLICE DEPARTMENT", "")
    text = text.replace("CRIME AND FIRE LOG/MEDIA BULLETIN", "")
    text = re.sub(r'[A-Z]+ \d+, \d+', '', text)  # Remove date headers

    # Remove structural text
    text = re.sub(r'Date Reported.*', '', text)
    text = re.sub(r'Incident/Case#.*', '', text)
    text = re.sub(r'Summary:.*', '', text)
    text = re.sub(r'Disposition:.*', '', text)

    # Clean up whitespace
    text = text.strip()

    return text


def extract_value(text, pattern):
    """Helper function to extract values using regex patterns"""
    match = re.search(pattern, text)
    return match.group(1).strip() if match else ""


if __name__ == "__main__":
    scrape_ucsd_police_logs()