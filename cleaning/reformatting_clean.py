
import pandas as pd
import numpy as np
import re
import os

'''
Can be used for files with null values in rows that should be all one row. Used for cleaning:
- UCLA
- UCBerkley
- UCF
'''


def clean_crime_log(input_file, output_file=None, config=None):
    if output_file is None:
        file_name, file_ext = os.path.splitext(input_file)
        output_file = f"{file_name}_cleaned{file_ext}"

    default_config = {
        "case_id_patterns": ["case", "event", "incident", "#", "number", "report"],
        "location_patterns": ["location", "address", "place"],
        "date_patterns": ["date", "time", "occur", "reported", "from", "to"],
        "crime_patterns": ["crime", "type", "offense", "incident", "event"],
        "disposition_patterns": ["disposition", "status"],
        "metadata_patterns": [
            r"\*MANUALLY ADDED / EDITED", r"Page \d+ of \d+", r"APDC  \(Rev\.",
            r"Print Date:", r"\*\*VAWA PROTECTION"
        ],
        "standardize_disposition": True,
        "remove_dates_from_disposition": True,
        "title_case": False,
        "min_header_matches": 2
    }

    if config:
        default_config.update(config)

    config = default_config
    print(f"Reading file: {input_file}")

    df = read_csv_file(input_file)
    if df is None:
        print("Error: Could not read the file.")
        return None

    print(f"Original shape: {df.shape}")

    cleaned_df = process_crime_log(df, config)
    cleaned_df.to_csv(output_file, index=False)
    print(f"Cleaned data saved to: {output_file}")

    return cleaned_df


def read_csv_file(input_file):
    try:
        df = pd.read_csv(input_file, encoding='utf-8')
        return df
    except Exception as e:
        for encoding in ['latin1', 'iso-8859-1', 'cp1252']:
            try:
                df = pd.read_csv(input_file, encoding=encoding)
                return df
            except Exception:
                pass

        try:
            with open(input_file, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()

            temp_file = input_file + ".temp"
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.writelines(lines)

            df = pd.read_csv(temp_file)
            os.remove(temp_file)
            return df
        except Exception:
            return None


def process_crime_log(df, config):
    unnamed_cols = [col for col in df.columns if 'Unnamed' in str(col) or str(col).strip() == '']
    if unnamed_cols:
        df = df.drop(columns=unnamed_cols)

    df.columns = clean_column_names(df.columns)
    df = remove_metadata_and_headers(df, config)
    case_column = identify_case_column(df, config["case_id_patterns"])
    cleaned_df = combine_related_entries(df, case_column, config)
    cleaned_df = perform_additional_cleaning(cleaned_df, config)

    if config["title_case"]:
        cleaned_df = apply_title_case(cleaned_df)

    return cleaned_df


def clean_column_names(columns):
    cleaned_columns = []
    for col in columns:
        cleaned_col = str(col).replace('20', ' ')
        cleaned_col = cleaned_col.rstrip(':').strip()
        cleaned_col = re.sub(r'\s+', ' ', cleaned_col)
        cleaned_columns.append(cleaned_col)

    return cleaned_columns


def remove_metadata_and_headers(df, config):
    rows_to_remove = []

    for i, row in df.iterrows():
        row_values = [str(val).strip() for val in row.values if pd.notna(val)]
        row_text = ' '.join(row_values)

        if any(re.search(pattern, row_text) for pattern in config["metadata_patterns"]):
            rows_to_remove.append(i)
            continue

        column_matches = 0
        for val in row_values:
            if any(val.lower() in col.lower() for col in df.columns):
                column_matches += 1

        if column_matches >= config["min_header_matches"]:
            rows_to_remove.append(i)
            continue

    if rows_to_remove:
        df = df.drop(rows_to_remove)

    return df


def identify_case_column(df, case_patterns):
    for pattern in case_patterns:
        for col in df.columns:
            if pattern.lower() in col.lower():
                return col

    if len(df.columns) > 0:
        return df.columns[0]

    return None


def combine_related_entries(df, case_column, config):
    if not case_column:
        return df

    cleaned_df = pd.DataFrame(columns=df.columns)

    i = 0
    while i < len(df):
        current_row = df.iloc[i].copy()

        if pd.notna(current_row[case_column]) and str(current_row[case_column]).strip() != '':
            combined_values = {col: current_row[col] for col in df.columns}

            j = i + 1
            while j < len(df) and (pd.isna(df.iloc[j][case_column]) or str(df.iloc[j][case_column]).strip() == ''):
                for col in df.columns:
                    if pd.notna(df.iloc[j][col]) and str(df.iloc[j][col]).strip() != '':
                        if pd.isna(combined_values[col]) or str(combined_values[col]).strip() == '':
                            combined_values[col] = df.iloc[j][col]
                        else:
                            col_lower = col.lower()

                            if any(pattern in col_lower for pattern in config["location_patterns"]):
                                combined_values[col] = f"{combined_values[col]}, {df.iloc[j][col]}"

                            elif any(pattern in col_lower for pattern in config["crime_patterns"]):
                                combined_values[col] = f"{combined_values[col]} {df.iloc[j][col]}"

                            elif any(pattern in col_lower for pattern in config["date_patterns"]):
                                if "range" in col_lower or "from" in col_lower or "to" in col_lower or "between" in col_lower:
                                    combined_values[col] = f"{combined_values[col]} - {df.iloc[j][col]}"
                                else:
                                    combined_values[col] = df.iloc[j][col]

                            else:
                                combined_values[col] = f"{combined_values[col]} {df.iloc[j][col]}"

                j += 1

            cleaned_df = pd.concat([cleaned_df, pd.DataFrame([combined_values])], ignore_index=True)
            i = j
        else:
            cleaned_df = pd.concat([cleaned_df, pd.DataFrame([current_row])], ignore_index=True)
            i += 1

    return cleaned_df


def perform_additional_cleaning(df, config):
    cleaned_df = df.copy()

    for col in cleaned_df.columns:
        cleaned_df[col] = cleaned_df[col].astype(str).str.strip()
        cleaned_df[col] = cleaned_df[col].replace('nan', '')

        if any(pattern in col.lower() for pattern in config["disposition_patterns"]):
            if config["remove_dates_from_disposition"]:
                cleaned_df[col] = remove_dates_and_times(cleaned_df[col])

            if config["standardize_disposition"]:
                cleaned_df[col] = standardize_disposition_values(cleaned_df[col])

            cleaned_df.loc[cleaned_df[col].isin(['', ' ', 'None']), col] = 'Unknown'

        elif any(pattern in col.lower() for pattern in config["crime_patterns"]):
            cleaned_df[col] = standardize_crime_types(cleaned_df[col])

    return cleaned_df


def remove_dates_and_times(series):
    date_patterns = [
        r'\d{1,2}/\d{1,2}/\d{2,4}', r'\d{1,2}-\d{1,2}-\d{2,4}', r'\d{1,2}\.\d{1,2}\.\d{2,4}'
    ]
    time_patterns = [
        r'\d{1,2}:\d{2}(:\d{2})?(\s*[AP]M)?', r'\d{1,2}[AP]M'
    ]

    for pattern in date_patterns + time_patterns:
        series = series.str.replace(pattern, '', regex=True)

    series = series.str.replace(r'Inactive:\s*', 'Inactive', regex=True)
    series = series.str.replace(r'Closed:\s*', 'Closed', regex=True)
    series = series.str.replace(r'Open:\s*', 'Open', regex=True)
    series = series.str.replace(r'Pending:\s*', 'Pending', regex=True)

    series = series.str.replace(r'\s+', ' ', regex=True).str.strip()

    return series


def standardize_disposition_values(series):
    disposition_mapping = {
        'CLSD': 'CLOSED', 'Clsd': 'Closed', 'OPEN/ACTIVE': 'OPEN',
        'Open/Active': 'Open', 'PEND': 'PENDING', 'Pend': 'Pending',
        'UNFND': 'UNFOUNDED', 'Unfnd': 'Unfounded', 'INACTIVE': 'INACTIVE',
        'Inact': 'Inactive', 'REFERRED': 'REFERRED', 'REF': 'REFERRED'
    }

    for old, new in disposition_mapping.items():
        series = series.str.replace(r'\b' + old + r'\b', new, regex=True)

    return series


def standardize_crime_types(series):
    series = series.str.replace('Related', '').str.strip()

    crime_mapping = {
        'BURG': 'BURGLARY', 'Burg': 'Burglary', 'AUTO BURG': 'AUTO BURGLARY',
        'Auto Burg': 'Auto Burglary', 'THEFT FM MTR': 'THEFT FROM MOTOR VEHICLE',
        'Theft Fm Mtr': 'Theft From Motor Vehicle', 'ASLT': 'ASSAULT',
        'Aslt': 'Assault', 'HARR': 'HARASSMENT', 'Harr': 'Harassment',
        'DUI': 'DRIVING UNDER INFLUENCE', 'MVA': 'MOTOR VEHICLE ACCIDENT',
        'Mva': 'Motor Vehicle Accident', 'Caslty-Alcoh': 'Casualty-Alcohol',
        'Found Prop.': 'Found Property'
    }

    for old, new in crime_mapping.items():
        series = series.str.replace(r'\b' + old + r'\b', new, regex=True)

    return series


def apply_title_case(df):
    title_case_df = df.copy()

    for col in title_case_df.columns:
        if title_case_df[col].dtype == 'object':
            title_case_df[col] = title_case_df[col].apply(
                lambda x: x.title() if pd.notna(x) and x.lower() != 'nan' and x != '' else x
            )

            common_abbr = {
                'Id': 'ID', 'Ssn': 'SSN', 'Dob': 'DOB', 'Usa': 'USA',
                'Uk': 'UK', 'Ucla': 'UCLA', 'Uc': 'UC', 'Pd': 'PD', 'Dui': 'DUI'
            }

            for old, new in common_abbr.items():
                title_case_df[col] = title_case_df[col].str.replace(
                    r'\b' + old + r'\b', new, regex=True
                )

    return title_case_df


if __name__ == "__main__":
    input_file = "input.csv"
    clean_crime_log(input_file)