// Global variables
let globalData = {};
let availableFiles = [
  "BentleyUniversity.csv",
  "GCU.csv",
  "GeorgiaState.csv",
  "ProvidenceCollege.csv",
  "StanfordUniversity.csv",
  "UMiami.csv",
  "UniversityOfColorado.csv"
];

// Initialize the dashboard
document.addEventListener('DOMContentLoaded', function() {
    console.log("Yearly Dashboard initializing...");
    
    // Create error container
    createErrorContainer();
    
    // Load available files
    loadAvailableFiles();
    
    // Set up event listeners
    document.getElementById('applyDateFilters').addEventListener('click', updateVisualizations);
    document.getElementById('applyTimeCrimeFilter').addEventListener('click', updateVisualizations);
});

// Helper function to create error container
function createErrorContainer() {
    if (!document.getElementById('errorContainer')) {
        const container = document.createElement('div');
        container.id = 'errorContainer';
        container.style.color = 'red';
        container.style.padding = '10px';
        container.style.margin = '10px 0';
        container.style.border = '1px solid red';
        container.style.backgroundColor = '#fff0f0';
        container.style.display = 'none';
        
        const loadingMessage = document.getElementById('loadingMessage');
        if (loadingMessage) {
            loadingMessage.parentNode.insertBefore(container, loadingMessage.nextSibling);
        } else {
            // If no loading message, add to body
            document.body.appendChild(container);
        }
    }
}

// Load available CSV files from hardcoded array
function loadAvailableFiles() {
    console.log("Loading available files...");
    
    // Populate the file selector dropdown
    const fileSelector = document.getElementById('fileSelector');
    fileSelector.innerHTML = ''; // Clear existing options
    
    // Add special "Combine All Files" option at the beginning
    const combineOption = document.createElement('option');
    combineOption.value = "Combine All Files";
    combineOption.textContent = "Combine All Files";
    fileSelector.appendChild(combineOption);
    
    // Add all individual files
    availableFiles.forEach(file => {
        const option = document.createElement('option');
        option.value = file;
        option.textContent = file.replace('.csv', ''); // Remove .csv extension for display
        fileSelector.appendChild(option);
    });
    
    // Add event listener after populating options
    fileSelector.addEventListener('change', handleFileSelection);
    
    // Select the first file by default
    handleFileSelection();
}

// Handle file selection change
function handleFileSelection() {
    const selectedFile = document.getElementById('fileSelector').value;
    console.log(`Attempting to load file: ${selectedFile}`);
    
    document.getElementById('loadingMessage').style.display = 'block';
    
    if (document.getElementById('errorContainer')) {
        document.getElementById('errorContainer').style.display = 'none';
    }
    
    // Check if the file exists in the list
    if (selectedFile !== 'Combine All Files' && !availableFiles.includes(selectedFile)) {
        console.error(`Selected file "${selectedFile}" is not in the availableFiles array`);
    }
    
    // Load the selected data file
    loadData(selectedFile)
        .then(data => {
            if (!data || !data.records || data.records.length === 0) {
                throw new Error('No valid data records were loaded');
            }
            
            globalData = data;
            console.log("Data loaded successfully:", data.records.length, "records");
            
            // Debug data
            debugData(data);
            
            populateSelectors(data);
            updateVisualizations();
            document.getElementById('loadingMessage').style.display = 'none';
        })
        .catch(error => {
            console.error('Error loading data:', error);
            document.getElementById('loadingMessage').style.display = 'none';
            
            // Show error to user
            const errorContainer = document.getElementById('errorContainer');
            if (errorContainer) {
                errorContainer.textContent = `Error: ${error.message}`;
                errorContainer.style.display = 'block';
            } else {
                alert(`Error loading data: ${error.message}`);
            }
        });
}

// Load data from CSV file
function loadData(filename) {
    return new Promise((resolve, reject) => {
        if (filename === 'Combine All Files') {
            // Load and combine all files from the availableFiles array
            const allFilesPromises = availableFiles.map(file => {
                return loadSingleFile(file).catch(error => {
                    console.warn(`Error loading ${file}:`, error);
                    return []; // Return empty array for this file
                });
            });
            
            Promise.all(allFilesPromises)
                .then(results => {
                    let allRecords = [].concat(...results);
                    if (allRecords.length === 0) {
                        reject(new Error("Failed to load any data files. Please check your data directory structure."));
                    } else {
                        resolve({ records: allRecords, filename: filename });
                    }
                })
                .catch(error => reject(error));
        } else {
            // Load a single file
            loadSingleFile(filename)
                .then(records => {
                    resolve({ records: records, filename: filename });
                })
                .catch(error => reject(error));
        }
    });
}

// Helper function to load a single file
function loadSingleFile(filename) {
    return new Promise((resolve, reject) => {
        // Try multiple possible paths
        const possiblePaths = [
            `data/yearly/${filename}`,
            `./data/yearly/${filename}`,
            `../data/yearly/${filename}`,
        ];
        
        console.log(`Trying to load ${filename} from possible paths:`, possiblePaths);
        
        // Function to try loading from different paths
        function tryNextPath(pathIndex) {
            if (pathIndex >= possiblePaths.length) {
                reject(new Error(`Failed to load ${filename} from all attempted paths`));
                return;
            }
            
            const path = possiblePaths[pathIndex];
            console.log(`Attempting to load from ${path}`);
            
            fetch(path)
                .then(response => {
                    if (!response.ok) {
                        console.warn(`Failed to load ${filename} from ${path} (${response.status}: ${response.statusText})`);
                        return tryNextPath(pathIndex + 1);
                    }
                    console.log(`Successfully loaded ${filename} from ${path}`);
                    return response.text();
                })
                .then(text => {
                    if (!text) return; // Skip if previous step returned undefined (went to next path)
                    
                    console.log(`Parsing CSV data for ${filename} (first 100 chars):`, text.substring(0, 100));
                    
                    try {
                        // Parse CSV data using Papa Parse
                        const result = Papa.parse(text, { header: true, dynamicTyping: true });
                        
                        if (result.errors && result.errors.length > 0) {
                            console.warn(`Warnings parsing ${filename}:`, result.errors);
                        }
                        
                        const validRecords = result.data.filter(record => 
                            record && Object.keys(record).length > 1)
                            .map(record => ({...record, 'Source File': filename}));
                            
                        if (validRecords.length === 0) {
                            console.error(`File ${filename} was loaded but contains no valid data records`);
                            reject(new Error(`File ${filename} contains no valid data records`));
                        } else {
                            console.log(`Successfully parsed ${validRecords.length} records from ${filename}`);
                            resolve(validRecords);
                        }
                    } catch (parseError) {
                        console.error(`Error parsing CSV data for ${filename}:`, parseError);
                        reject(new Error(`Error parsing CSV file: ${parseError.message}`));
                    }
                })
                .catch(error => {
                    console.error(`Network error loading ${filename} from ${path}:`, error);
                    tryNextPath(pathIndex + 1);
                });
        }
        
        tryNextPath(0);
    });
}

// Debugging helper function
function debugData(data) {
    console.log("Data sample:", data.records.slice(0, 3));
    console.log("Number of records:", data.records.length);
    
    if (data.records.length > 0) {
        console.log("Available fields:", Object.keys(data.records[0]));
        
        // Check if required fields exist
        const requiredFields = ['Year', 'Criminal Offenses'];
        const missingFields = requiredFields.filter(field => !Object.keys(data.records[0]).includes(field));
        
        if (missingFields.length > 0) {
            console.warn("Missing required fields:", missingFields);
        }
    } else {
        console.error("No records loaded!");
    }
}

// Populate selectors
function populateSelectors(data) {
    // Crime types
    const crimeTypes = [...new Set(data.records.map(record => record['Criminal Offenses']))];
    crimeTypes.sort();
    
    const crimeTypeSelector = document.getElementById('crimeTypeSelector');
    crimeTypeSelector.innerHTML = '<option value="All Crimes">All Crimes</option>';
    
    crimeTypes.forEach(crimeType => {
        const option = document.createElement('option');
        option.value = crimeType;
        option.textContent = crimeType;
        crimeTypeSelector.appendChild(option);
    });
    
    // Years
    const years = [...new Set(data.records.map(record => record['Year']))];
    years.sort();
    
    const yearSelector = document.getElementById('yearSelector');
    yearSelector.innerHTML = '<option value="All Years">All Years</option>';
    
    years.forEach(year => {
        const option = document.createElement('option');
        option.value = year;
        option.textContent = year;
        yearSelector.appendChild(option);
    });
    
    // Locations
    const locations = [
        'Residential Facility',
        'Non Residential Facility',
        'Public Property',
        'Non Campus Building or Property'
    ];
    
    const locationSelector = document.getElementById('locationSelector');
    locationSelector.innerHTML = '';
    
    locations.forEach(location => {
        if (data.records.some(record => location in record)) {
            const option = document.createElement('option');
            option.value = location;
            option.textContent = location;
            locationSelector.appendChild(option);
        }
    });
    
    // Select first location by default if none is selected
    if (locationSelector.selectedIndex === -1 && locationSelector.options.length > 0) {
        locationSelector.selectedIndex = 0;
    }
}

// Update all visualizations
function updateVisualizations() {
    // Get selected values
    const selectedCrimeType = document.getElementById('crimeTypeSelector').value;
    const selectedYear = document.getElementById('yearSelector').value;
    const selectedLocation = document.getElementById('locationSelector').value;
    
    // Create visualizations
    createCrimeTypeDistribution(globalData.records);
    createYearlyTrends(globalData.records, selectedCrimeType);
    createLocationComparison(globalData.records, selectedYear);
    createCrimeCategoryAnalysis(globalData.records);
    createYearOverYearAnalysis(globalData.records, selectedLocation);
    createTotalOffensesByLocation(globalData.records);
}

// Create crime type distribution visualization
function createCrimeTypeDistribution(data) {
    // Sum up incidents by crime type across all locations
    const crimeTypeTotals = {};
    
    data.forEach(record => {
        const crimeType = record['Criminal Offenses'];
        const locations = [
            'Residential Facility',
            'Non Residential Facility',
            'Public Property',
            'Non Campus Building or Property'
        ];
        
        let total = 0;
        locations.forEach(loc => {
            if (record[loc] !== undefined) {
                total += parseInt(record[loc]);
            }
        });
        
        crimeTypeTotals[crimeType] = (crimeTypeTotals[crimeType] || 0) + total;
    });
    
    // Convert to array for plotting
    const plotData = Object.entries(crimeTypeTotals)
        .map(([type, count]) => ({type, count}))
        .sort((a, b) => b.count - a.count);
    
    // Create visualization
    const plotlyData = [{
        x: plotData.map(item => item.type),
        y: plotData.map(item => item.count),
        type: 'bar',
        marker: {
            color: 'rgba(55, 128, 191, 0.7)',
            line: {
                color: 'rgba(55, 128, 191, 1.0)',
                width: 1
            }
        }
    }];
    
    const layout = {
        title: 'Crime Type Distribution (All Years)',
        xaxis: {
            title: 'Crime Type',
            tickangle: -45
        },
        yaxis: {
            title: 'Number of Incidents'
        },
        margin: {
            b: 150
        },
        autosize: true
    };
    
    Plotly.newPlot('crimeDistributionChart', plotlyData, layout, {responsive: true});
}

// Create yearly trends visualization
function createYearlyTrends(data, crimeType) {
    // Filter by crime type if specified
    if (crimeType && crimeType !== "All Crimes") {
        data = data.filter(record => record['Criminal Offenses'] === crimeType);
    }
    
    // Group by year and sum incidents
    const yearlyTotals = {};
    
    data.forEach(record => {
        const year = record['Year'];
        const locations = [
            'Residential Facility',
            'Non Residential Facility',
            'Public Property',
            'Non Campus Building or Property'
        ];
        
        let total = 0;
        locations.forEach(loc => {
            if (record[loc] !== undefined) {
                total += parseInt(record[loc]);
            }
        });
        
        yearlyTotals[year] = (yearlyTotals[year] || 0) + total;
    });
    
    // Create array for plotting
    const years = Object.keys(yearlyTotals).sort();
    const counts = years.map(year => yearlyTotals[year]);
    
    // Create title
    const title = crimeType && crimeType !== "All Crimes" ?
        `Yearly Crime Trends: ${crimeType}` :
        'Yearly Crime Trends (All Types)';
    
    // Create visualization
    const plotlyData = [{
        x: years,
        y: counts,
        type: 'scatter',
        mode: 'lines+markers',
        marker: {
            color: 'rgba(55, 128, 191, 0.7)',
            size: 10
        },
        line: {
            color: 'rgba(55, 128, 191, 1.0)',
            width: 2
        }
    }];
    
    const layout = {
        title: title,
        xaxis: {
            title: 'Year',
            tickmode: 'linear',
            dtick: 1
        },
        yaxis: {
            title: 'Number of Incidents'
        },
        autosize: true
    };
    
    Plotly.newPlot('yearlyTrendsChart', plotlyData, layout, {responsive: true});
}

// Create location comparison visualization
function createLocationComparison(data, year) {
    // Filter by year if specified
    if (year && year !== "All Years") {
        data = data.filter(record => record['Year'] == year);
    }
    
    // Sum incidents by location
    const locationTotals = {};
    const locations = [
        'Residential Facility',
        'Non Residential Facility',
        'Public Property',
        'Non Campus Building or Property'
    ];
    
    locations.forEach(location => {
        locationTotals[location] = 0;
    });
    
    data.forEach(record => {
        locations.forEach(location => {
            if (record[location] !== undefined) {
                locationTotals[location] += parseInt(record[location]);
            }
        });
    });
    
    // Create title
    const title = year && year !== "All Years" ?
        `Crime Incidents by Location (${year})` :
        'Crime Incidents by Location (All Years)';
    
    // Create visualization
    const plotlyData = [{
        x: Object.keys(locationTotals),
        y: Object.values(locationTotals),
        type: 'bar',
        marker: {
            color: Object.values(locationTotals),
            colorscale: 'Viridis'
        }
    }];
    
    const layout = {
        title: title,
        xaxis: {
            title: 'Campus Location',
            tickangle: -45
        },
        yaxis: {
            title: 'Number of Incidents'
        },
        autosize: true
    };
    
    Plotly.newPlot('locationComparisonChart', plotlyData, layout, {responsive: true});
}

// Create crime category analysis
function createCrimeCategoryAnalysis(data) {
    // Define crime categories
    const violentCrimes = ['Murder', 'Rape', 'Robbery', 'Aggravated Assault'];
    const propertyCrimes = ['Burglary', 'Motor Vehicle Theft', 'Arson', 'Theft', 'Vandalism'];
    const drugAlcohol = ['Drug Law Violations', 'Liquor Law Violations', 'Drug Arrests', 'Alcohol Arrests'];
    const otherCrimes = ['Weapons Possession', 'Hate Crimes', 'Stalking', 'Dating Violence', 'Domestic Violence'];
    
    // Function to categorize a crime
    function categorize(crime) {
        if (violentCrimes.some(vc => crime.includes(vc))) return 'Violent Crimes';
        if (propertyCrimes.some(pc => crime.includes(pc))) return 'Property Crimes';
        if (drugAlcohol.some(da => crime.includes(da))) return 'Drug/Alcohol Violations';
        if (otherCrimes.some(oc => crime.includes(oc))) return 'Other Crimes';
        return 'Miscellaneous';
    }
    
    // Count incidents by category
    const categoryTotals = {
        'Violent Crimes': 0,
        'Property Crimes': 0,
        'Drug/Alcohol Violations': 0,
        'Other Crimes': 0,
        'Miscellaneous': 0
    };
    
    data.forEach(record => {
        const category = categorize(record['Criminal Offenses']);
        const locations = [
            'Residential Facility',
            'Non Residential Facility',
            'Public Property',
            'Non Campus Building or Property'
        ];
        
        let total = 0;
        locations.forEach(loc => {
            if (record[loc] !== undefined) {
                total += parseInt(record[loc]);
            }
        });
        
        categoryTotals[category] += total;
    });
    
    // Create visualization
    const plotlyData = [{
        values: Object.values(categoryTotals),
        labels: Object.keys(categoryTotals),
        type: 'pie',
        hole: 0.3,
        marker: {
            colors: [
                'rgba(219, 64, 82, 0.7)',   // Violent - red
                'rgba(55, 128, 191, 0.7)',  // Property - blue
                'rgba(50, 171, 96, 0.7)',   // Drug/Alcohol - green
                'rgba(128, 0, 128, 0.7)',   // Other - purple
                'rgba(128, 128, 128, 0.7)'  // Misc - gray
            ]
        }
    }];
    
    const layout = {
        title: 'Crime Category Distribution',
        autosize: true
    };
    
    Plotly.newPlot('crimeCategoryChart', plotlyData, layout, {responsive: true});
}

// Create year-over-year analysis visualization
function createYearOverYearAnalysis(data, location) {
    // Group by year for the selected location
    const yearlyTotals = {};
    
    data.forEach(record => {
        const year = record['Year'];
        
        if (record[location] !== undefined) {
            yearlyTotals[year] = (yearlyTotals[year] || 0) + parseInt(record[location]);
        }
    });
    
    // Create arrays for plotting
    const years = Object.keys(yearlyTotals).sort();
    const counts = years.map(year => yearlyTotals[year]);
    
    // Calculate percent changes
    const percentChanges = [];
    for (let i = 1; i < counts.length; i++) {
        const change = ((counts[i] - counts[i-1]) / counts[i-1]) * 100;
        percentChanges.push(change);
    }
    
    // Create visualization
    const plotlyData = [{
        x: years,
        y: counts,
        type: 'scatter',
        mode: 'lines+markers',
        marker: {
            color: 'rgba(55, 128, 191, 0.7)',
            size: 10
        },
        line: {
            color: 'rgba(55, 128, 191, 1.0)',
            width: 2
        }
    }];
    
    const layout = {
        title: `Year-over-Year Crime Trends: ${location}`,
        xaxis: {
            title: 'Year',
            tickmode: 'linear',
            dtick: 1
        },
        yaxis: {
            title: 'Number of Incidents'
        },
        annotations: [],
        autosize: true
    };
    
    // Add percent change annotations
    for (let i = 0; i < percentChanges.length; i++) {
        const pct = percentChanges[i];
        const direction = pct > 0 ? "↑" : "↓";
        const color = pct > 0 ? "red" : "green";
        
        layout.annotations.push({
            x: years[i+1],
            y: counts[i+1],
            text: `${direction} ${Math.abs(pct).toFixed(1)}%`,
            showarrow: true,
            arrowhead: 4,
            arrowsize: 1,
            arrowwidth: 2,
            arrowcolor: color,
            yshift: 10
        });
    }
    
    Plotly.newPlot('yearOverYearChart', plotlyData, layout, {responsive: true});
}

// Create total offenses by location visualization
function createTotalOffensesByLocation(data) {
    // Group by year and location
    const yearLocationTotals = {};
    const locations = [
        'Residential Facility',
        'Non Residential Facility',
        'Public Property',
        'Non Campus Building or Property'
    ];
    
    data.forEach(record => {
        const year = record['Year'];
        
        if (!yearLocationTotals[year]) {
            yearLocationTotals[year] = {};
            locations.forEach(loc => {
                yearLocationTotals[year][loc] = 0;
            });
        }
        
        locations.forEach(loc => {
            if (record[loc] !== undefined) {
                yearLocationTotals[year][loc] += parseInt(record[loc]);
            }
        });
    });
    
    // Create arrays for plotting
    const years = Object.keys(yearLocationTotals).sort();
    
    // Create stacked bar chart data
    const plotlyData = locations.map(location => {
        return {
            x: years,
            y: years.map(year => yearLocationTotals[year][location]),
            name: location,
            type: 'bar'
        };
    });
    
    const layout = {
        title: 'Total Offenses by Location and Year',
        xaxis: {
            title: 'Year',
            tickmode: 'linear',
            dtick: 1
        },
        yaxis: {
            title: 'Number of Incidents'
        },
        barmode: 'stack',
        legend: {
            orientation: 'h',
            y: -0.2
        },
        autosize: true
    };
    
    Plotly.newPlot('totalOffensesChart', plotlyData, layout, {responsive: true});
}
