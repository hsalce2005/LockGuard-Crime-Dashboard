# LockGuard-Crime-Dashboard-V1

# Campus Crime Dashboard

A web-based interactive dashboard for visualizing and analyzing campus crime data from various universities. This project aims to provide insights into campus safety trends, incident distributions, and crime patterns.

## Features

- **Interactive Data Selection**: Choose from multiple university datasets or combine them all
- **Comprehensive Visualizations**:
  - Incident Types Distribution
  - Reports Per Month (with date filtering)
  - Top Crime Locations
  - Day of Week Analysis
  - Time of Day Analysis
  - Incident Status Breakdown
  - Dollar Amount Analysis (for theft incidents)
- **Advanced Filtering**: Filter data by crime type, date range, and more
- **Responsive Design**: Works on desktop and mobile devices

## Setup Instructions

### Prerequisites

- Web server (can use VS Code Live Server extension for local development)
- Web browser (Chrome, Firefox, Safari, Edge)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/hsalce2005/LockGuard-Crime-Dashboard-V1.git
   cd LockGuard-Crime-Dashboard-V1
   ```

2. Create the proper directory structure:
   ```
   project-root/
   ├── daily-dashboard.html
   ├── yearly-dashboard.html
   ├── daily-dashboard.js
   ├── yearly-dashboard.js
   ├── data/
   │   ├── daily/
   │   │   └── [CSV files]
   │   └── yearly/
   │       └── [CSV files]
   ```

3. Place your CSV files in the appropriate data folders

4. Start a local server:
   - Using VS Code Live Server extension: Open the project in VS Code, right-click on an HTML file, and select "Open with Live Server"
   - Using Python: `python -m http.server` (Python 3) or `python -m SimpleHTTPServer` (Python 2)

5. Open your browser and navigate to the server address (typically http://127.0.0.1:5500 or http://localhost:8000)

## CSV Data Format

### Daily Dashboard Data Format

Data can be scraped using the Python scripts within the `webscrape` folder. If formatting is an issue after scraping, scripts within the `cleaning` folder.

CSV files for the daily dashboard should contain (at least) the following columns:
- `Incident Type`: Type of crime or incident
- `Date/Time Occurred`: Date and time of incident (format: YYYY-MM-DD HH:MM)
- `Location`: Where the incident occurred
- `Disposition`: Status of the case (e.g., Pending, Closed, Referred)

Example:
```csv
Incident Type,Date/Time Occurred,Location,Disposition
Theft Under $500,2023-01-15 14:30,Residential Facility,Closed
Vandalism,2023-01-16 08:45,Public property - On Campus,Pending
```

### Yearly Dashboard Data Format

CSV files for the yearly dashboard should contain (at least) the following columns:
- `Year`: Year the incidents were recorded
- `Criminal Offenses`: Type of crime
- `Residential Facility`: Number of incidents in residential facilities
- `Non Residential Facility`: Number of incidents in non-residential facilities
- `Public Property`: Number of incidents on public property
- `Non Campus Building or Property`: Number of incidents in off-campus university properties

Example:
```csv
Year,Criminal Offenses,Residential Facility,Non Residential Facility,Public Property,Non Campus Building or Property
2022,Burglary,5,2,0,1
2022,Liquor Law Violations,12,3,2,0
```

## Customizing the Dashboard

### Adding New Universities

1. Add your CSV file to the appropriate data folder (daily or yearly)
2. Update the `availableFiles` array in the corresponding JavaScript file:

```javascript
let availableFiles = [
  // Existing files...
  "YourUniversity.csv"
];
```

## Technologies Used

- HTML/CSS/JavaScript
- [Plotly.js](https://plotly.com/javascript/) for interactive charts
- [Papa Parse](https://www.papaparse.com/) for CSV parsing
- [Bootstrap](https://getbootstrap.com/) for responsive design


## Acknowledgments

- University police departments for providing public safety data
- Campus safety organizations for promoting transparency in crime reporting
- Open source community for the libraries used in this project
  
