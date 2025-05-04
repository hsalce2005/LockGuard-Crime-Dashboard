import pandas as pd
import re
import os

# Path to your existing CSV file
input_csv = "crimelog_csvs/Crime-Fire-Log-1.csv"

# Create output folder
output_folder = "cleaned_data"
os.makedirs(output_folder, exist_ok=True)

# Define your custom column name mapping here
custom_column_names = {
    'Date_Reported': 'Date/Time Reported',
    'Case_Number': 'Case Number',
    'Crime_Information': 'Crime Information',
    'Location': 'Location',
    'Status': 'Status'
}

print(f"Reading data from {input_csv}...")

# Read the CSV file
df = pd.read_csv(input_csv)

# Print the original columns for debugging
print("Original columns:")
print(df.columns.tolist())
print(f"Original shape: {df.shape}")


# Function to identify column types based on content
def identify_columns(df):
    column_mapping = {}

    for col in df.columns:
        # Sample some values to determine column type
        sample_values = df[col].dropna().astype(str).str.strip().head(20).tolist()

        if not sample_values:
            continue

        # Date column check
        date_patterns = [
            r'\d{1,2}/\d{1,2}/\d{4}',  # MM/DD/YYYY
            r'\d{1,2}-\d{1,2}-\d{4}'  # MM-DD-YYYY
        ]

        date_col = any(re.search(pattern, str(val)) for pattern in date_patterns for val in sample_values[:5])

        # Case number check
        case_pattern = r'\d{4}-\d{5}'
        case_col = any(re.search(case_pattern, str(val)) for val in sample_values[:5])

        # Status check
        status_terms = ['active', 'closed', 'pending', 'investigation', 'arrest']
        status_col = any(any(term in str(val).lower() for term in status_terms) for val in sample_values[:5])

        # Crime information check
        crime_terms = ['theft', 'assault', 'burglary', 'robbery', 'harassment', 'trespass']
        crime_col = any(any(term in str(val).lower() for term in crime_terms) for val in sample_values[:5])

        # Location check
        location_terms = ['street', 'st', 'ave', 'road', 'rd', 'hall', 'building', 'bldg']
        location_col = any(any(term in str(val).lower() for term in location_terms) for val in sample_values[:5])

        # Assign column type based on checks
        if date_col and 'Date_Reported' not in column_mapping.values():
            column_mapping[col] = "Date_Reported"
        elif case_col and 'Case_Number' not in column_mapping.values():
            column_mapping[col] = "Case_Number"
        elif crime_col and 'Crime_Information' not in column_mapping.values():
            column_mapping[col] = "Crime_Information"
        elif location_col and 'Location' not in column_mapping.values():
            column_mapping[col] = "Location"
        elif status_col and 'Status' not in column_mapping.values():
            column_mapping[col] = "Status"

    return column_mapping


# Try to automatically identify columns
column_mapping = identify_columns(df)
print("Identified columns:")
for old_col, new_col in column_mapping.items():
    print(f"{old_col} -> {new_col}")

# If we have duplicate mappings or missing columns, use a manual mapping
manual_mapping = False
standard_columns = ['Date_Reported', 'Case_Number', 'Crime_Information', 'Location', 'Status']
missing_columns = [col for col in standard_columns if col not in column_mapping.values()]
duplicate_columns = [col for col in standard_columns if list(column_mapping.values()).count(col) > 1]

if missing_columns or duplicate_columns:
    print("Column identification issue detected.")
    if missing_columns:
        print(f"Missing columns: {missing_columns}")
    if duplicate_columns:
        print(f"Duplicate columns: {duplicate_columns}")

    print("Switching to manual column mapping...")
    # Manual mapping based on the order we expect
    column_mapping = {
        '0': 'Date_Reported',
        '1': 'Case_Number',
        '2': 'Crime_Information',
        '3': 'Location',
        '4': 'Status'
    }
    manual_mapping = True

# Create a new DataFrame with renamed columns
renamed_df = pd.DataFrame()

# Apply the column mapping
for old_col, new_col in column_mapping.items():
    if old_col in df.columns:
        renamed_df[new_col] = df[old_col]

# Ensure we have all the required columns
for col in standard_columns:
    if col not in renamed_df.columns:
        renamed_df[col] = ""


# Function to extract first datetime from a string
def extract_first_datetime(date_str):
    if pd.isna(date_str) or date_str == "":
        return ""

    date_str = str(date_str)

    # Extract date with time from formats like "04/29/25 8:15am - 04/29/25 5:00pm"
    datetime_pattern = r'(\d{1,2}/\d{1,2}/\d{2,4})\s*(\d{1,2}:\d{2}\s*[aApP][mM])'
    datetime_match = re.search(datetime_pattern, date_str)

    if datetime_match:
        date_part = datetime_match.group(1)
        time_part = datetime_match.group(2)
        return f"{date_part} {time_part}"

    # Try to extract just a date if no time is found
    date_pattern = r'(\d{1,2}/\d{1,2}/\d{2,4})'
    date_match = re.search(date_pattern, date_str)

    if date_match:
        return date_match.group(1)

    return date_str


# Function to convert text from ALL CAPS to Title Case
def convert_to_title_case(text):
    if pd.isna(text) or text == "":
        return ""

    text = str(text)

    # Don't convert certain terms that should remain uppercase
    uppercase_terms = ["am", "pm", "atm", "id", "dps", "upenn", "penn"]

    # Convert text to title case
    words = text.lower().split()
    title_case_words = []

    for word in words:
        # Check if word should remain uppercase
        if word.lower() in uppercase_terms:
            title_case_words.append(word.upper())
        else:
            # Convert word to title case
            title_case_words.append(word.capitalize())

    return " ".join(title_case_words)


# Apply date formatting
renamed_df['Date_Reported'] = renamed_df['Date_Reported'].apply(lambda x: extract_first_datetime(x))

# Clean up all columns by removing extra spaces and standardizing
for col in renamed_df.columns:
    renamed_df[col] = renamed_df[col].astype(str).str.strip()
    renamed_df[col] = renamed_df[col].replace(r'\s+', ' ', regex=True)  # Replace multiple spaces with one
    renamed_df[col] = renamed_df[col].replace('nan', '')

    # Convert text from ALL CAPS to Title Case
    if col in ['Crime_Information', 'Location', 'Status']:
        renamed_df[col] = renamed_df[col].apply(convert_to_title_case)

# Remove rows with empty or invalid Case_Number
# This assumes that a valid case number has the format YYYY-NNNNN
valid_case_number = renamed_df['Case_Number'].str.match(r'\d{4}-\d{5}')
renamed_df = renamed_df[valid_case_number]

# Select only the essential columns and order them
final_df = renamed_df[standard_columns]

# Apply custom column names if specified
final_df = final_df.rename(columns=custom_column_names)

# Save the cleaned data
output_csv = os.path.join(output_folder, "upenn_crime_log_cleaned.csv")
final_df.to_csv(output_csv, index=False)
print(f"Saved cleaned data to {output_csv}")

output_excel = os.path.join(output_folder, "upenn_crime_log_cleaned.xlsx")
final_df.to_excel(output_excel, index=False)
print(f"Saved cleaned data to {output_excel}")

# Print a sample of the cleaned data
print("\nSample of cleaned data:")
print(final_df.head())