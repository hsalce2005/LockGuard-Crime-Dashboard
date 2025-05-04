import pandas as pd
import sys

# For files that have blank rows/rows with cells that need to be included in the row above
def combine_rows(csv_file, output_file):
    df = pd.read_csv(csv_file, header=None)

    if len(df) % 2 != 0:
        df.loc[len(df)] = [None] * len(df.columns)

    for i in range(0, len(df), 2):
        df.iloc[i] = df.iloc[i].astype(str).fillna('') + ' ' + df.iloc[i + 1].astype(str).fillna('')

    df = df.iloc[::2].reset_index(drop=True)

    df.to_csv(output_file, index=False, header=False)
    print(f"Processed file saved as {output_file}")


if __name__ == "__main__":
    combine_rows(
        "UCBerkley.csv",
        "output.csv")
    if len(sys.argv) < 3:
        print("Usage: python script.py input.csv output.csv")
    else:
        combine_rows(sys.argv[1], sys.argv[2])
