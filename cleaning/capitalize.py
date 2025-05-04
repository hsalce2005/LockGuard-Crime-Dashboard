import pandas as pd

def correct_capitalization(text):
    if text.isupper():
        return text.title()
    return text

def process_csv(input_file, output_file, columns):
    df = pd.read_csv(input_file)
    for column in columns:
        if column in df.columns:
            df[column] = df[column].astype(str).apply(correct_capitalization)
        else:
            print(f"Column '{column}' not found in the CSV file.")
    df.to_csv(output_file, index=False)
    print(f"Processed file saved as: {output_file}")

input_csv = "UniversityOfSouthCarolina_cleaned.csv"
output_csv = "output.csv"
columns_to_process = ["Initial_Incident", "Location"]

process_csv(input_csv, output_csv, columns_to_process)
