#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
from bs4 import BeautifulSoup
import csv

# Use for simple webpages

url = ""
response = requests.get(url)

# make sure request worked
if response.status_code == 200:
    soup = BeautifulSoup(response.content, 'html.parser')

    crime_table = soup.find('table')
    if crime_table:
        rows = crime_table.find_all('tr')

        with open('crime_log.csv', 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['Date', 'Incident Type', 'Location', 'Status'])

            for row in rows[1:]:
                columns = row.find_all('td')
                if columns:
                    date = columns[0].get_text(strip=True)
                    incident_type = columns[1].get_text(strip=True)
                    location = columns[2].get_text(strip=True)
                    status = columns[3].get_text(strip=True)

                    writer.writerow([date, incident_type, location, status])

        print("Data saved to 'crime_log.csv'")
    else:
        print("Crime log table not found on the page.")
else:
    print(f"Failed to fetch the URL. Status code: {response.status_code}")
