import re
import csv
import os
import pdfplumber


def extract_text_from_pdf(pdf_path):
    """Extract text from PDF file using pdfplumber"""
    full_text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                full_text += page.extract_text() + "\n"
        return full_text
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return ""


def clean_text(text):
    """Clean up text by removing extra whitespace and normalizing line breaks"""
    text = re.sub(r'\s+', ' ', text)  # Replace multiple spaces with a single space
    text = text.replace(' \n ', '\n').replace('\n ', '\n').replace(' \n', '\n')  # Clean line breaks
    return text


def parse_crime_log(text):
    """Parse crime log text and extract crime incidents"""
    incidents = []

    # this regex captures each incident block
    incident_blocks = re.findall(r'Date Reported:\s+(.+?)(?=Date Reported:|$)', text, re.DOTALL)

    print(f"Found {len(incident_blocks)} potential incident blocks")

    for i, block in enumerate(incident_blocks):
        full_block = "Date Reported: " + block

        try:
            case_match = re.search(r'Report #:\s*(\d+-\d+)', full_block)
            if not case_match:
                print(f"Skipping block {i + 1}: No case number found")
                continue

            case_number = case_match.group(1).strip()

            date_reported_match = re.search(r'Date Reported:\s+([\d/]+)\s+-\s+\w+\s+at\s+([\d:]+)', full_block)
            if date_reported_match:
                month, day, year = date_reported_match.group(1).split('/')
                time = date_reported_match.group(2)
                date_reported = f"{int(month)}/{int(day)}/{year} {time}"
            else:
                print(f"Warning: Could not extract date reported for case {case_number}")
                date_reported = ""

            location_match = re.search(r'General Location:\s+([^\n]+)', full_block)
            location = location_match.group(1).strip() if location_match else ""

            date_occurred_match = re.search(r'Date Occurred From:\s+([\d/]+)\s+-\s+\w+\s+at\s+([\d:]+)', full_block)
            if date_occurred_match:
                occurred_date = date_occurred_match.group(1)
                occurred_time = date_occurred_match.group(2)
                date_occurred = f"{occurred_date} {occurred_time}"
            else:
                date_occurred = ""

            incident_match = re.search(r'Incident/Offenses:\s+([^\n]+)', full_block)
            if incident_match:
                incident_type = incident_match.group(1).strip().title()
            else:
                incident_type = ""

            disp_match = re.search(r'Disposition:\s+([^\n]+)', full_block)
            if disp_match:
                disposition = disp_match.group(1).strip().title()
            else:
                disposition = ""

            incident = {
                'Case Number': case_number,
                'Date/Time Reported': date_reported,
                'Incident Type': incident_type,
                'Date/Time Occurred': date_occurred,
                'Location': location,
                'Disposition': disposition
            }

            incidents.append(incident)

        except Exception as e:
            print(f"Error parsing block {i + 1}: {e}")

    print(f"Successfully parsed {len(incidents)} incidents")
    return incidents


def write_to_csv(incidents, output_path):
    """Write incidents to CSV file"""
    if not incidents:
        print("No incidents to write.")
        return

    with open(output_path, 'w', newline='', encoding='utf-8') as file:
        fieldnames = ['Case Number', 'Date/Time Reported', 'Incident Type',
                      'Date/Time Occurred', 'Location', 'Disposition']
        writer = csv.DictWriter(file, fieldnames=fieldnames)

        writer.writeheader()
        for incident in incidents:
            writer.writerow(incident)

    print(f"Successfully wrote {len(incidents)} incidents to {output_path}")


def main():
    input_pdf = ""
    output_csv = "crime_data.csv"

    # Check if the PDF file exists
    if not os.path.exists(input_pdf):
        print(f"Error: The file {input_pdf} does not exist.")
        return

    print(f"Reading PDF from {input_pdf}...")
    text = extract_text_from_pdf(input_pdf)

    if not text:
        print("Error: Could not extract text from the PDF.")
        return

    # save extracted text to a file for debugging
    with open("extracted_text.txt", "w", encoding="utf-8") as f:
        f.write(text)
    print("Saved extracted text to extracted_text.txt for debugging")

    incidents = parse_crime_log(text)
    write_to_csv(incidents, output_csv)


if __name__ == "__main__":
    main()