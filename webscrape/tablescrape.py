import requests
from bs4 import BeautifulSoup
import pandas as pd

'''
Script to scrape websites where there the table is directly on webpage. Used for:
- NYU
- Indiana University
'''

url = "___"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
}

response = requests.get(url, headers=headers)

if response.status_code == 200:
    soup = BeautifulSoup(response.text, "html.parser")
    print("Successfully accessed the webpage!")
else:
    print(f"Failed to access page: {response.status_code}")

response.raise_for_status()  # Raise an error if request fails

soup = BeautifulSoup(response.text, 'html.parser')

table = soup.find("table")

headers = [th.text.strip() for th in table.find_all("th")]

rows = []
for tr in table.find_all("tr")[1:]:  # Skip header row
    cells = [td.text.strip() for td in tr.find_all("td")]
    if cells:
        rows.append(cells)

df = pd.DataFrame(rows, columns=headers)

df.to_csv("jan.csv", index=False)

