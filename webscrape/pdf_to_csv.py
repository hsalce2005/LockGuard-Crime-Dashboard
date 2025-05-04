import re
import csv
import sys
import argparse
from PyPDF2 import PdfReader

'''
Script that converts downloaded PDF files --> CSV files (must download these PDFs first). Used for:
- Northeastern University
- Texas A&M
- UCDavis
'''

def extract_crime_data(pdf_path):
    reader = PdfReader(pdf_path)
    all_records = []

    for page_num in range(len(reader.pages)):
        page = reader.pages[page_num]
        text = page.extract_text()

        lines = text.split('\n')
        start_processing = False

        for line in lines:
            if re.match(r'^(25-\d{5}|25RC\d{5})', line.strip()):
                start_processing = True

            if start_processing:
                # Extract incident information using regex patterns (adjust as needed)
                incident_match = re.match(r'^(25-\d{5}|25RC\d{5})\s+(.*?)\s+(\d{2}/\d{2}/\d{2}\s+\d{4}Hrs)(.*)$',
                                          line.strip())

                if incident_match:
                    incident_num = incident_match.group(1)
                    nature = incident_match.group(2).strip()
                    report_date = incident_match.group(3).strip()

                    remaining = incident_match.group(4).strip()

                    # Pattern for occurrence date (adjust as needed)
                    occurrence_pattern = r'(\d{2}/\d{2}/\d{2}\s+\d{4}Hrs\s+-\s*\d{2}/\d{2}/\d{2}\s+\d{4}Hrs|\d{2}/\d{2}/\d{2}\s+\d{4}Hrs)'
                    occurrence_match = re.search(occurrence_pattern, remaining)

                    occurrence_date = ""
                    if occurrence_match:
                        occurrence_date = occurrence_match.group(1).strip()
                        remaining = remaining.replace(occurrence_date, "", 1).strip()

                    parts = remaining.strip().split("(CPN)")

                    location = parts[0].strip() + "(CPN)" if len(parts) > 0 else ""
                    disposition = parts[1].strip() if len(parts) > 1 else ""

                    record = {
                        "Incident Number": incident_num,
                        "Nature": nature,
                        "Report Date": report_date,
                        "Occurrence Date": occurrence_date,
                        "General Location": location,
                        "Disposition": disposition
                    }

                    all_records.append(record)

    return all_records


def save_to_csv(records, output_file):
    if not records:
        print("No records to save.")
        return

    fieldnames = ["Larceny Incident", "Date/Time Reported", "Date/Time Occured", "LOCATION", "DISPOSITION", "CASE NUMBER"]

    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)

    print(f"Successfully saved {len(records)} records to {output_file}")


def main():
    DEFAULT_PDF_PATH = "crimelog_pdfs/Crime_Log .pdf"
    DEFAULT_OUTPUT_PATH = "output.csv"

    if DEFAULT_PDF_PATH:
        try:
            print(f"Using built-in PDF path: {DEFAULT_PDF_PATH}")
            records = extract_crime_data(DEFAULT_PDF_PATH)
            save_to_csv(records, DEFAULT_OUTPUT_PATH)
            print(f"Data saved to {DEFAULT_OUTPUT_PATH}")
            return 0
        except Exception as e:
            print(f"Error processing PDF: {e}")
            return 1

    parser = argparse.ArgumentParser(description='Extract crime data from Rutgers PD PDF crime log')
    parser.add_argument('pdf_file', nargs='?', help='Path to the PDF file')
    parser.add_argument('--output', '-o', default='rutgers_crime_log.csv',
                        help='Output CSV file path (default: rutgers_crime_log.csv)')

    args = parser.parse_args()

    if not args.pdf_file:
        parser.print_help()
        return 1

    try:
        records = extract_crime_data(args.pdf_file)
        save_to_csv(records, args.output)
    except Exception as e:
        print(f"Error processing PDF: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())