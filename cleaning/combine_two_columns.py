import pandas as pd

# combine 2 columns
def combine_columns(input_csv, output_csv, col1, col2, new_col_name):
    df = pd.read_csv(input_csv)

    df[new_col_name] = df[col1].astype(str) + " " + df[col2].astype(str)

    # optional: drops the original two columns
    # df = df.drop(columns=[col1, col2])

    df.to_csv(output_csv, index=False)

combine_columns("UCon.csv", "UConn.csv", "Date/Time Occurred", "TimeO", "Date/Time Occurred")
