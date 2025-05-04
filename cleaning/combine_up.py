import pandas as pd

# Used for specific cases to combine rows up
df = pd.read_csv('crimelog.csv', header=None)

header_row = ['Nature | Classification', 'Case Number', 'Date/Time Reported', 'Date/Time Occured', 'Location Name', 'Street Name', 'Disposition']

df.dropna(how='all', inplace=True)
df.reset_index(drop=True, inplace=True)

header_indices = df[df.apply(lambda row: row.tolist() == header_row, axis=1)].index
if len(header_indices) > 1:
    df.drop(header_indices[1:], inplace=True)
    df.reset_index(drop=True, inplace=True)

rows_to_drop = set()
i = 1
while i < len(df):
    row = df.iloc[i]
    num_nulls = row.isnull().sum()
    if num_nulls > 2:
        for col_index, value in row.items():
            if pd.notnull(value):
                prev_value = str(df.at[i - 1, col_index]) if pd.notnull(df.at[i - 1, col_index]) else ''
                df.at[i - 1, col_index] = (prev_value + ' ' + str(value)).strip()
        rows_to_drop.add(i)
        if i + 1 < len(df):
            next_row = df.iloc[i + 1]
            next_nulls = next_row.isnull().sum()
            if next_nulls > 2:
                for col_index, value in next_row.items():
                    if pd.notnull(value):
                        prev_value = str(df.at[i - 1, col_index]) if pd.notnull(df.at[i - 1, col_index]) else ''
                        df.at[i - 1, col_index] = (prev_value + ' ' + str(value)).strip()
                rows_to_drop.add(i + 1)
                i += 1
    i += 1

df.drop(list(rows_to_drop), inplace=True)
df.reset_index(drop=True, inplace=True)

df.columns = df.iloc[0]
df = df[1:].reset_index(drop=True)

df.to_csv('cleaned_file.csv', index=False)

