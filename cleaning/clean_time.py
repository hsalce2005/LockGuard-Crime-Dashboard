import pandas as pd
import re


INPUT_FILE = "UVA.csv"
OUTPUT_FILE = "output.csv"
COLUMN_NAME = None  # name of the column containing times to format (enter None to apply to all columns)


# ===============================

def format_time_in_string(full_string):
    """
    Finds and formats time patterns within a string.

    Examples:
    - "2/17/25 906" -> "2/17/25 9:06"
    - "Meeting at 1230" -> "Meeting at 12:30"
    - "0836-0917 Conference" -> "08:36 Conference"
    - "12:00-12:30" -> "12:00"
    - "08:36-\n09:17" -> "08:36"
    - "12/4/2024-12/5/2024" -> "12/4/2024" (keeps date intact)
    - "00:00-23:59" -> "00:00"
    """
    if not isinstance(full_string, str):
        return full_string

    # Handle date ranges (like "12/4/2024-12/5/2024")
    # The pattern looks for date format with slashes and hyphen
    date_pattern = r'(\d{1,2}/\d{1,2}/\d{2,4})-\d{1,2}/\d{1,2}/\d{2,4}'
    full_string = re.sub(date_pattern, r'\1', full_string)

    # Handle time ranges with a newline between them (like "08:36-\n09:17")
    newline_pattern = r'(\d{1,2}:\d{2})-\s*\n\s*\d{1,2}:\d{2}'
    full_string = re.sub(newline_pattern, r'\1', full_string)

    # Handle time ranges without newline (like "12:00-12:30" or "00:00-23:59")
    hyphen_pattern = r'(\d{1,2}:\d{2})-\d{1,2}:\d{2}'
    full_string = re.sub(hyphen_pattern, r'\1', full_string)

    # NEW PATTERN: Handle specific format "0214 03-23-2025" -> "03/23/2025 02:14"
    special_format_pattern = r'(\d{4})\s+(\d{2})-(\d{2})-(\d{4})'
    if re.search(special_format_pattern, full_string):
        full_string = re.sub(special_format_pattern,
                             lambda m: f"{m.group(2)}/{m.group(3)}/{m.group(4)} {m.group(1)[:2]}:{m.group(1)[2:]}",
                             full_string)
        return full_string

    # Function to replace time matches with formatted times
    def replace_time(match):
        time_str = match.group(0)

        # If there's a hyphen with digits on both sides (like 0836-0917),
        # extract just the first part
        if '-' in time_str and re.search(r'\d+-\d+', time_str):
            time_str = time_str.split('-')[0]

        # Pad to ensure at least 3 digits (e.g., "45" -> "045")
        padded = time_str.zfill(3)

        # For 3 digits (e.g., "045"), format as H:MM
        if len(padded) == 3:
            return f"{padded[0]}:{padded[1:]}"

        # For 4 digits (e.g., "1230"), format as HH:MM
        elif len(padded) == 4:
            return f"{padded[:2]}:{padded[2:]}"

        # If no patterns match, return the original string
        return time_str

    # Find stand-alone time patterns (not part of longer numbers)
    # This pattern looks for:
    # 1. Numbers like 900, 1245 (3-4 digits) that aren't part of longer numbers
    # 2. Number ranges like 0900-1000
    pattern = r'\b(\d{3,4}(?:-\d{3,4})?)\b'

    # Replace all matching time patterns in the string
    result = re.sub(pattern, replace_time, full_string)

    return result


def process_csv(input_file, output_file, column_name=None):
    """
    Read a CSV file, format times in the specified column, and save to a new CSV.
    """
    try:
        # Read the CSV file
        df = pd.read_csv(input_file)

        if column_name is None:
            # Process all columns
            for column in df.columns:
                df[column] = df[column].apply(format_time_in_string)
        elif column_name in df.columns:
            # Process only the specified column
            df[column_name] = df[column_name].apply(format_time_in_string)
        else:
            # Column not found
            return False

        # Save the modified dataframe to a new CSV file
        df.to_csv(output_file, index=False)

        return True

    except Exception as e:
        # exception handling
        return False


def main():
    process_csv(INPUT_FILE, OUTPUT_FILE, COLUMN_NAME)


if __name__ == "__main__":
    main()