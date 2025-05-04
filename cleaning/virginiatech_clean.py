def format_time(time_str):
    """
    Format time string to HH:MM format and extract only the first time if multiple exist.

    Args:
        time_str (str): Time string to format (e.g., "1510", "0122-0400", "0")

    Returns:
        str: Formatted time string in HH:MM format
    """
    # Remove any whitespace
    time_str = str(time_str).strip()

    # If the time string is empty or just "0", return an empty string
    if not time_str or time_str == "0":
        return ""

    # If there are multiple times (e.g., "0122-0400"), take only the first one
    if "-" in time_str:
        time_str = time_str.split("-")[0].strip()

    # Try to extract a 3 or 4 digit time value using regex
    match = re.search(r'(\d{3,4})', time_str)
    if match:
        time_digits = match.group(1)

        # Pad to 4 digits if necessary
        if len(time_digits) == 3:
            time_digits = "0" + time_digits

        # Format as HH:MM
        try:
            hours = time_digits[:2]
            minutes = time_digits[2:]
            return f"{hours}:{minutes}"
        except:
            return time_str  # Return original if formatting fails

    return time_str  # Return original if no match



import pandas as pd
import sys
import re
from datetime import datetime


def combine_date_time(date_str, time_str):
    """
    Combine date and time strings into a single formatted string.

    Args:
        date_str (str): Date string (e.g., "1/3/25")
        time_str (str): Time string (e.g., "15:10")

    Returns:
        str: Combined date and time string
    """
    # Remove any whitespace
    date_str = str(date_str).strip()
    time_str = str(time_str).strip()

    # If either date or time is missing, return just the date
    if not date_str:
        return ""
    if not time_str:
        return date_str

    # Try to parse the date
    try:
        # First, standardize the date format (assuming MM/DD/YY format)
        if '/' in date_str:
            parts = date_str.split('/')
            if len(parts) == 3:
                month, day, year = parts
                # Ensure year has 4 digits
                if len(year) == 2:
                    # Assuming 20xx for years less than 50, and 19xx for years 50 and above
                    year_prefix = "20" if int(year) < 50 else "19"
                    year = year_prefix + year
                formatted_date = f"{month}/{day}/{year}"
            else:
                formatted_date = date_str
        else:
            formatted_date = date_str

        # Combine date with formatted time
        return f"{formatted_date} {time_str}"
    except:
        # If parsing fails, return the original date
        if time_str:
            return f"{date_str} {time_str}"
        return date_str


def clean_csv(input_file, output_file):
    """
    Clean and reformat the Virginia Tech CSV file according to the preferred format.

    Parameters:
    input_file (str): Path to the input CSV file
    output_file (str): Path to save the cleaned CSV file
    """
    try:
        # Read the CSV file with more robust error handling
        print(f"Reading file: {input_file}")

        # Try different parsing options to handle potential issues
        try:
            # First attempt: standard parsing
            df = pd.read_csv(input_file)
        except Exception as e1:
            print(f"Standard parsing failed: {e1}")
            try:
                # Second attempt: with error_bad_lines=False (skip bad lines)
                df = pd.read_csv(input_file, on_bad_lines='skip')
                print("Used lenient parsing (skipping bad lines)")
            except Exception as e2:
                print(f"Lenient parsing failed: {e2}")
                try:
                    # Third attempt: with engine='python' (more flexible but slower)
                    df = pd.read_csv(input_file, engine='python')
                    print("Used Python engine for parsing")
                except Exception as e3:
                    print(f"Python engine parsing failed: {e3}")
                    try:
                        # Fourth attempt: try with a different delimiter
                        df = pd.read_csv(input_file, sep='\t', on_bad_lines='skip', engine='python')
                        print("Used tab delimiter for parsing")
                    except Exception as e4:
                        raise Exception(f"All parsing attempts failed: {e1}, {e2}, {e3}, {e4}")

        # Display original information
        print(f"Original shape: {df.shape}")
        print(f"Original columns: {list(df.columns)}")

        # Rename columns to match the desired format
        column_mapping = {
            "Date Reported": "Date/Time Reported",
            "Criminal Offense": "Incident Type",
            "Occurrence Date(s)": "Date/Time Occurr"
        }

        # Check if the expected columns exist
        for old_col in column_mapping.keys():
            if old_col not in df.columns:
                print(f"Warning: Column '{old_col}' not found in the CSV")

        # Only rename columns that exist
        rename_dict = {k: v for k, v in column_mapping.items() if k in df.columns}
        df = df.rename(columns=rename_dict)

        # Strip whitespace from all string columns
        for col in df.columns:
            if df[col].dtype == 'object':
                df[col] = df[col].str.strip()

        # Format the Time(s) column if it exists
        if "Time(s)" in df.columns:
            df["Time(s)"] = df["Time(s)"].astype(str).apply(lambda x: format_time(x))

            # Combine Date/Time Occurr with the formatted Time(s) if both columns exist
            if "Date/Time Occurr" in df.columns:
                df["Date/Time Occurr"] = df.apply(
                    lambda row: combine_date_time(row["Date/Time Occurr"], row["Time(s)"]),
                    axis=1
                )

                # Remove the Time(s) column as it's now part of Date/Time Occurr
                df = df.drop(columns=["Time(s)"])
            elif "Occurrence Date(s)" in df.columns:
                # If we haven't renamed yet
                df["Occurrence Date(s)"] = df.apply(
                    lambda row: combine_date_time(row["Occurrence Date(s)"], row["Time(s)"]),
                    axis=1
                )
                df = df.rename(columns={"Occurrence Date(s)": "Date/Time Occurr"})
                df = df.drop(columns=["Time(s)"])

        # Handle the Case# formatting (if column exists)
        if "Case#" in df.columns:
            df["Case#"] = df["Case#"].str.replace(" ", " ")  # This line ensures consistent spacing

        # Save the cleaned data
        print(f"Saving cleaned file to: {output_file}")
        df.to_csv(output_file, index=False)

        # Display some statistics about the cleaned data
        print(f"Cleaned shape: {df.shape}")
        print(f"Cleaned columns: {list(df.columns)}")
        print(f"First few rows of cleaned data:")
        print(df.head())

        return True

    except Exception as e:
        print(f"Error: {e}")
        return False


if __name__ == "__main__":
    # Check if command line arguments are provided
    if len(sys.argv) >= 3:
        input_file = sys.argv[1]
        output_file = sys.argv[2]
    else:
        # Default filenames if no command line arguments
        input_file = "VirginiaTech(clean).csv"
        output_file = "VirginiaTech_formatted.csv"

    # Run the cleaning function
    success = clean_csv(input_file, output_file)

    if success:
        print("CSV cleaning completed successfully!")
    else:
        print("CSV cleaning failed.")