import pandas as pd
import re
import os
import numpy as np


def fix_crime_log_data(input_file="crimelog_data.xlsx", output_file="crimelog_data_fixed.xlsx"):
    """
    Fix the UConn crime log data where nature and location are reversed or combined.

    The issue identified:
    - Column 5 contains both Location and Nature separated by a newline character
    - Location is typically the first part, and Nature is the second part
    - In some cases, Nature appears standalone without Location

    This script separates them into two distinct columns and handles various inconsistencies.
    """
    print(f"Reading data from {input_file}...")

    # Read the Excel file
    df = pd.read_excel(input_file)

    print(f"Original DataFrame shape: {df.shape}")
    print(f"Original column names: {list(df.columns)}")

    # Initialize new DataFrame with same structure as original
    fixed_df = df.copy()

    # Identify the problematic column (column 5 in 0-indexed system)
    problem_col_index = 5

    # If new columns don't yet exist, create them
    if 'Nature' not in fixed_df.columns:
        fixed_df['Nature'] = None
    if 'Location' not in fixed_df.columns:
        fixed_df['Location'] = None

    # Pattern for identifying address-like strings
    address_pattern = re.compile(
        r'^\d+|^[A-Z]+\s+\d+|STREET|ROAD|AVE|RD|ST|DRIVE|DR|LANE|LN|CIRCLE|PATH|BUILDING|HALL|CAMPUS|WAY')

    # Process each row
    for idx in range(len(fixed_df)):
        cell_value = df.iloc[idx, problem_col_index] if problem_col_index < df.shape[1] else None

        # Skip if the cell is empty
        if pd.isna(cell_value) or cell_value is None or str(cell_value).strip() == '':
            continue

        cell_value = str(cell_value).strip()

        # Check if the cell contains a newline
        if '\n' in cell_value:
            parts = cell_value.split('\n')

            # Determine which part is location and which is nature
            # In UConn data, typically first part is location and second is nature
            first_part = parts[0].strip()
            second_part = parts[1].strip() if len(parts) > 1 else ""

            # Address pattern check to validate our assumption
            if address_pattern.search(first_part):
                location = first_part
                nature = second_part
            else:
                # If first part doesn't look like an address, it might be nature
                nature = first_part
                location = second_part

            # Special handling for header row
            if "Nature" in first_part and "Location" in second_part or "Location" in first_part and "Nature" in second_part:
                continue

            # Set the values in the new columns
            fixed_df.at[idx, 'Location'] = location
            fixed_df.at[idx, 'Nature'] = nature
        else:
            # For single values, determine if it's nature or location
            if address_pattern.search(cell_value):
                fixed_df.at[idx, 'Location'] = cell_value
            else:
                fixed_df.at[idx, 'Nature'] = cell_value

    # Drop the original combined column if needed
    # fixed_df = fixed_df.drop(columns=[df.columns[problem_col_index]])

    # Clean up any remaining inconsistencies
    # Ensure "Nature" column doesn't contain location information
    for idx, row in fixed_df.iterrows():
        nature_val = str(row['Nature']) if not pd.isna(row['Nature']) else ''

        # If nature contains address-like information, move it to location
        if address_pattern.search(nature_val):
            fixed_df.at[idx, 'Location'] = nature_val
            fixed_df.at[idx, 'Nature'] = None

    # Save the fixed dataframe
    print(f"Saving fixed data to {output_file}...")
    fixed_df.to_excel(output_file, index=False)

    print(f"Data fixing complete! Check {output_file} for the fixed data.")
    return fixed_df


if __name__ == "__main__":
    # If run as a script, process the default file
    fix_crime_log_data()

    # Example of how to run with custom files:
    # fix_crime_log_data("input.xlsx", "output.xlsx")