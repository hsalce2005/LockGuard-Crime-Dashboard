import pandas as pd
import re
from datetime import datetime


def clean_usc_crime_log(input_file, output_file):
    # Read the CSV file
    df = pd.read_csv(input_file, header=None)

    # Identify the actual header rows (appears to be row 7 based on analysis)
    header_row_index = None
    for i in range(min(20, len(df))):
        if isinstance(df.iloc[i, 0], str) and "Date Reported" in df.iloc[i, 0]:
            header_row_index = i
            break

    if header_row_index is None:
        print("Could not find header row. Using default headers.")
        df.columns = ['Date_Reported', 'Event_Case_Offense', 'Initial_Incident',
                      'Final_Incident', 'Date_From', 'Date_To', 'Location',
                      'Disposition', 'Extra1', 'Extra2']
    else:
        # Extract the actual headers
        headers = []
        for col in range(df.shape[1]):
            if col < len(df.iloc[header_row_index]) and pd.notna(df.iloc[header_row_index, col]):
                header = df.iloc[header_row_index, col]
                # Clean up header if needed
                header = re.sub(r'\s+', '_', header.strip())
                header = re.sub(r'[^a-zA-Z0-9_]', '', header)
                # Convert to title case for headers
                header = header.title()
                headers.append(header)
            else:
                headers.append(f'Extra{col}')

        # Set column names
        df.columns = headers

        # Remove header rows and other non-data rows
        df = df.iloc[header_row_index + 1:].reset_index(drop=True)

    # Create a new dataframe to store clean data
    clean_df = pd.DataFrame(columns=df.columns)

    # Process rows, handling multi-line entries
    current_entry = {}
    for i in range(len(df)):
        row = df.iloc[i]

        # Check if this is a new entry (usually starts with a date in the first column)
        if isinstance(row.iloc[0], str) and re.match(r'\d{2}/\d{2}/\d{2}\s+-\s+[A-Z]{3}', str(row.iloc[0])):
            # Save previous entry if it exists
            if current_entry:
                clean_df = pd.concat([clean_df, pd.DataFrame([current_entry])], ignore_index=True)

            # Start a new entry
            current_entry = {col: row.iloc[idx] for idx, col in enumerate(df.columns)}
        elif current_entry:  # This is a continuation of the previous entry
            # Append non-null values to the corresponding fields in the current entry
            for idx, col in enumerate(df.columns):
                if pd.notna(row.iloc[idx]) and row.iloc[idx] != '':
                    if pd.notna(current_entry[col]) and current_entry[col] != '':
                        # Append to existing value
                        current_entry[col] = str(current_entry[col]) + " " + str(row.iloc[idx])
                    else:
                        # Set new value
                        current_entry[col] = row.iloc[idx]

    # Add the last entry
    if current_entry:
        clean_df = pd.concat([clean_df, pd.DataFrame([current_entry])], ignore_index=True)

    # Clean up specific fields
    date_cols = [col for col in clean_df.columns if 'date' in col.lower()]
    for date_col in date_cols:
        if date_col in clean_df.columns:
            # Standardize date format
            clean_df[date_col] = clean_df[date_col].apply(
                lambda x: standardize_date(x) if pd.notna(x) else None
            )

    # Clean Location field - remove "Campus" and standardize
    location_col = next((col for col in clean_df.columns if 'location' in col.lower()), None)
    if location_col:
        clean_df[location_col] = clean_df[location_col].apply(
            lambda x: clean_location(x) if pd.notna(x) else None
        )

    # Clean Disposition field
    disposition_col = next((col for col in clean_df.columns if 'disposition' in col.lower()), None)
    if disposition_col:
        clean_df[disposition_col] = clean_df[disposition_col].apply(
            lambda x: x.strip() if isinstance(x, str) else x
        )

    # Drop rows that are still headers or irrelevant information
    date_reported_col = next(
        (col for col in clean_df.columns if 'date_reported' in col.lower() or 'datereported' in col.lower()), None)
    if date_reported_col:
        clean_df = clean_df[
            ~clean_df[date_reported_col].astype(str).str.lower().str.contains('date reported|daily crime|from:',
                                                                              na=False)]

    # Drop duplicate rows
    clean_df = clean_df.drop_duplicates().reset_index(drop=True)

    # Remove any "#NAME?" values (likely Excel errors)
    clean_df = clean_df.replace("#NAME?", None)

    # Convert all string columns to proper capitalization
    for col in clean_df.columns:
        clean_df[col] = clean_df[col].apply(
            lambda x: convert_to_proper_case(x) if isinstance(x, str) else x
        )

    # Save cleaned data
    clean_df.to_csv(output_file, index=False)
    print(f"Cleaned data saved to {output_file}")

    # Print summary statistics
    print(f"Original rows: {len(df)}")
    print(f"Cleaned rows: {len(clean_df)}")
    print(f"Removed rows: {len(df) - len(clean_df)}")
    print("\nMissing values by column:")
    for col in clean_df.columns:
        missing = clean_df[col].isna().sum()
        print(f"  {col}: {missing} ({missing / len(clean_df) * 100:.1f}%)")


def convert_to_proper_case(text):
    """
    Convert text to proper capitalization:
    - Convert all-caps text to title case with some improvements
    - Preserve certain abbreviations
    """
    if not isinstance(text, str):
        return text

    # Skip dates
    if re.match(r'\d{4}-\d{2}-\d{2}', text):
        return text

    # Check if text is all uppercase
    if text.isupper() or (sum(1 for c in text if c.isupper()) / len(text) > 0.7):
        # Convert to lowercase first
        text = text.lower()

        # Split by hyphens and handle each part separately
        parts = re.split(r'(\s*-\s*)', text)
        for i in range(0, len(parts), 2):
            if i < len(parts):
                # Title case for each part (capitalize first letter of each word)
                words = parts[i].split()
                for j in range(len(words)):
                    if words[j]:
                        # Skip articles, conjunctions, and prepositions unless they're the first word
                        if j > 0 and words[j] in ['a', 'an', 'the', 'and', 'but', 'or', 'for', 'nor', 'on', 'at', 'to',
                                                  'from', 'by', 'with', 'in', 'of']:
                            continue
                        words[j] = words[j][0].upper() + words[j][1:]
                parts[i] = ' '.join(words)

        text = ''.join(parts)

        # Fix common abbreviations
        abbr_patterns = [
            (r'\b(id)\b', 'ID'),
            (r'\b(usa)\b', 'USA'),
            (r'\b(goa)\b', 'GOA'),
            (r'\b(usc)\b', 'USC'),
            (r'\b(ca)\b', 'CA'),
            (r'\b(dps)\b', 'DPS'),
            (r'\b(pd)\b', 'PD'),
            (r'\b(la)\b', 'LA'),
            (r'\b(n/a)\b', 'N/A')
        ]

        for pattern, replacement in abbr_patterns:
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

        return text

    # For mixed case text, just return as is
    return text


def standardize_date(date_str):
    """Standardize date strings to YYYY-MM-DD format"""
    if not isinstance(date_str, str):
        return date_str

    # Handle various date formats
    date_part = date_str.split(' - ')[0] if ' - ' in date_str else date_str
    date_part = date_part.split(' at ')[0] if ' at ' in date_part else date_part

    # Try to parse the date
    try:
        if re.match(r'\d{2}/\d{2}/\d{2}', date_part):
            # Format MM/DD/YY
            dt = datetime.strptime(date_part, '%m/%d/%y')
            return dt.strftime('%Y-%m-%d')
        elif re.match(r'\d{2}/\d{2}/\d{4}', date_part):
            # Format MM/DD/YYYY
            dt = datetime.strptime(date_part, '%m/%d/%Y')
            return dt.strftime('%Y-%m-%d')
    except ValueError:
        pass

    # If parsing fails, return the original string
    return date_str


def clean_location(location_str):
    """Clean up location field"""
    if not isinstance(location_str, str):
        return location_str

    # Remove "- On Campus" and similar suffixes
    location = re.sub(r'\s*-\s*On\s+Campus\s*$', '', location_str, flags=re.IGNORECASE)

    # Standardize spacing
    location = ' '.join(location.split())

    return location


if __name__ == "__main__":
    input_file = "60-Day-5-2.csv"
    output_file = "cali.csv"
    clean_usc_crime_log(input_file, output_file)