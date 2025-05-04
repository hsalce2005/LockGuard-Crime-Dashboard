// Global variables
let globalData = {};
let availableFiles = [
  "ArizonaStateUniversity.csv",
  "BostonUniversity.csv",
  "DrexelUniversity.csv",
  "EmoryUniversity.csv",
  "FIU.csv",
  "GeorgiaTech.csv",
  "HarvardUniversity.csv",
  "IndianaUniversity.csv",
  "MichiganStateUniversity.csv",
  "NortheasternUniversity.csv",
  "NYU.csv",
  "OhioState.csv",
  "PennState.csv",
  "PrincetonUniversity.csv",
  "PurdueUniversity.csv",
  "QuinnipiacUniversity.csv",
  "RutgersUniversity.csv",
  "TempleUniversity.csv",
  "TexasA&M.csv",
  "UCDavis.csv",
  "UCRiverside.csv",
  "UChicago.csv",
  "UniversityOfCincinnatti.csv",
  "UCLA.csv",
  "UCSD.csv",
  "UniversityOfFlorida.csv",
  "UMich.csv",
  "UniversityOfArizona.csv",
  "UniversityOfMinnesota.csv",
  "UniversityOfNewMexico.csv",
  "UniversityOfWashington.csv",
  "UPenn.csv",
  "USC.csv",
  "UniversityOfVirginia.csv",
  "VirginiaTech.csv",
  "UniversityOfWisconsin-Madison.csv"
];

// Initialize the dashboard
document.addEventListener('DOMContentLoaded', function() {
    console.log("Dashboard initializing...");
    
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
            
            populateCrimeTypes(data);
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
            `data/daily/${filename}`,
            `./data/daily/${filename}`,
            `../data/daily/${filename}`,
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
                    if (!text) return; // Skip if previous step returned undefined 
                    
                    console.log(`Parsing CSV data for ${filename} (first 100 chars):`, text.substring(0, 100));
                    
                    try {
                        // Parse CSV data using Papa Parse with more robust options
                        const result = Papa.parse(text, { 
                            header: true, 
                            dynamicTyping: true, 
                            skipEmptyLines: true,
                            delimitersToGuess: [',', '\t', '|', ';'] // Try different delimiters
                        });
                        
                        if (result.errors && result.errors.length > 0) {
                            console.warn(`Warnings parsing ${filename}:`, result.errors);
                        }
                        
                        // Clean up column names by trimming whitespace
                        if (result.meta && result.meta.fields) {
                            const trimmedFieldsMap = {};
                            result.meta.fields.forEach(field => {
                                trimmedFieldsMap[field] = field.trim();
                            });
                            
                            // Apply trimmed field names to data
                            result.data = result.data.map(record => {
                                const cleanedRecord = {};
                                Object.keys(record).forEach(key => {
                                    const cleanKey = key.trim();
                                    cleanedRecord[cleanKey] = record[key];
                                });
                                return cleanedRecord;
                            });
                        }
                        
                        const validRecords = result.data
                            .filter(record => record && Object.keys(record).length > 1)
                            .map(record => {
                                // Add source file and ensure all records have the same structure
                                return {
                                    ...record, 
                                    'Source File': filename,
                                    // Ensure critical fields exist
                                    'Incident Type': record['Incident Type'] || 'Unknown',
                                    'Date/Time Occurred': record['Date/Time Occurred'] || 'Unknown',
                                    'Location': record['Location'] || 'Unknown',
                                    'Disposition': record['Disposition'] || 'Unknown'
                                };
                            });
                            
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

        const requiredFields = ['Incident Type', 'Date/Time Occurred', 'Location', 'Disposition'];
        const missingFields = requiredFields.filter(field => !Object.keys(data.records[0]).includes(field));
        
        if (missingFields.length > 0) {
            console.warn("Missing required fields:", missingFields);
        }
    } else {
        console.error("No records loaded!");
    }
}


function populateCrimeTypes(data) {
    // Get all unique incident types, filter out nulls and empty strings
    const crimeTypes = [...new Set(
        data.records
            .map(record => record['Incident Type'])
            .filter(type => type !== null && type !== undefined && type !== '')
    )];
    crimeTypes.sort();

    const crimeTypeSelector = document.getElementById('crimeTypeSelector');
    const timeCrimeTypeSelector = document.getElementById('timeCrimeTypeSelector');
    
    // Clear existing options
    crimeTypeSelector.innerHTML = '<option value="">All Crime Types</option>';
    timeCrimeTypeSelector.innerHTML = '<option value="">All Crime Types</option>';
    
    // Add options
    crimeTypes.forEach(crimeType => {
        if (crimeType) { // Additional check to ensure value isn't empty
            const option1 = document.createElement('option');
            option1.value = crimeType;
            option1.textContent = crimeType;
            crimeTypeSelector.appendChild(option1);
            
            const option2 = document.createElement('option');
            option2.value = crimeType;
            option2.textContent = crimeType;
            timeCrimeTypeSelector.appendChild(option2);
        }
    });
    
    setupDateSelectors(data);
}


function setupDateSelectors(data) {
    // Extract dates and find min/max, handling possible null values
    const dates = data.records
        .map(record => {
            if (!record['Date/Time Occurred']) return null;
            const datePart = record['Date/Time Occurred'].split(' ')[0];
            const date = new Date(datePart);
            // Check if date is valid
            return isNaN(date.getTime()) ? null : date;
        })
        .filter(date => date !== null);
    
    dates.sort((a, b) => a - b);
    
    if (dates.length === 0) {
        console.warn("No valid dates found in the data");
        return;
    }
    
    const minDate = dates[0];
    const maxDate = dates[dates.length - 1];
    
    // Generate array of year-month strings
    const months = [];
    const currentDate = new Date(minDate);
    
    while (currentDate <= maxDate) {
        const yearMonth = `${currentDate.getFullYear()}-${String(currentDate.getMonth() + 1).padStart(2, '0')}`;
        months.push(yearMonth);

        currentDate.setMonth(currentDate.getMonth() + 1);
    }
    
    // Populate start date selector
    const startDateSelector = document.getElementById('startDateSelector');
    startDateSelector.innerHTML = '';
    
    // Clear dropdown
    const startDateDropdown = document.getElementById('startDateDropdown');
    startDateDropdown.innerHTML = '<li><a class="dropdown-item" href="#" onclick="document.getElementById(\'startDateSelector\').value=\'\'; return false;">Clear</a></li>';
    
    // Add min and max attributes to input
    startDateSelector.min = months[0];
    startDateSelector.max = months[months.length - 1];
    
    // Populate dropdown
    months.forEach(month => {
        const item = document.createElement('li');
        const link = document.createElement('a');
        link.className = 'dropdown-item';
        link.href = '#';
        link.textContent = month;
        link.onclick = function() {
            startDateSelector.value = month;
            return false;
        };
        item.appendChild(link);
        startDateDropdown.appendChild(item);
    });
    
    // Populate end date selector
    const endDateSelector = document.getElementById('endDateSelector');
    endDateSelector.innerHTML = '';
    
    // Clear dropdown
    const endDateDropdown = document.getElementById('endDateDropdown');
    endDateDropdown.innerHTML = '<li><a class="dropdown-item" href="#" onclick="document.getElementById(\'endDateSelector\').value=\'\'; return false;">Clear</a></li>';
    
    // Add min and max attributes to input
    endDateSelector.min = months[0];
    endDateSelector.max = months[months.length - 1];
    
    // Populate dropdown
    months.forEach(month => {
        const item = document.createElement('li');
        const link = document.createElement('a');
        link.className = 'dropdown-item';
        link.href = '#';
        link.textContent = month;
        link.onclick = function() {
            endDateSelector.value = month;
            return false;
        };
        item.appendChild(link);
        endDateDropdown.appendChild(item);
    });
}


function updateVisualizations() {
    const selectedCrimeType = document.getElementById('crimeTypeSelector').value;
    const selectedTimeCrimeType = document.getElementById('timeCrimeTypeSelector').value;
    const startDate = document.getElementById('startDateSelector').value;
    const endDate = document.getElementById('endDateSelector').value;

    createIncidentTypeDistribution(globalData.records);
    createReportsPerMonth(globalData.records, selectedCrimeType, startDate, endDate);
    createLocationHeatmap(globalData.records);
    createDayOfWeekAnalysis(globalData.records);
    createTimeAnalysis(globalData.records, selectedTimeCrimeType);
    createIncidentStatusBreakdown(globalData.records);
    createDollarAmountVisualization(globalData.records);
}

function createIncidentTypeDistribution(data) {
    const incidentCounts = {};
    data.forEach(record => {
        // Skip if incident type is missing
        if (!record['Incident Type']) return;
        
        const type = record['Incident Type'];
        incidentCounts[type] = (incidentCounts[type] || 0) + 1;
    });

    const plotData = Object.entries(incidentCounts)
        .map(([type, count]) => ({ type, count }))
        .filter(item => item.count > 1)
        .sort((a, b) => b.count - a.count);
    
    // If no data, display a message
    if (plotData.length === 0) {
        displayNoDataMessage('incidentDistributionChart', 'No incident type data available');
        return;
    }
    
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
        title: 'Incident Types Distribution',
        xaxis: {
            title: 'Incident Type',
            tickangle: -45,
            automargin: true
        },
        yaxis: {
            title: 'Count'
        },
        margin: {
            b: 120, 
            l: 50,   
            r: 50,   
            t: 80   
        },
        height: 500,
        width: 1200,  
        autosize: false
    };
    
    const config = {
        responsive: true,
        scrollZoom: true
    };
    
    Plotly.newPlot('incidentDistributionChart', plotlyData, layout, config);
}

// Handle no data available scenario
function displayNoDataMessage(chartId, message) {
    const chartDiv = document.getElementById(chartId);
    if (chartDiv) {
        Plotly.newPlot(chartId, [], {
            title: message,
            annotations: [{
                text: message,
                x: 0.5,
                y: 0.5,
                xref: 'paper',
                yref: 'paper',
                showarrow: false,
                font: {
                    size: 16,
                    color: '#666'
                }
            }]
        });
    }
}

function createReportsPerMonth(data, crimeType, startDate, endDate) {
    // Filter by crime type if specified, ensuring we skip null values
    if (crimeType) {
        data = data.filter(record => record['Incident Type'] === crimeType);
    }
    
    const monthCounts = {};
    data.forEach(record => {
        // Skip if date is missing or invalid
        if (!record['Date/Time Occurred']) return;
        
        // Handle potential date parsing issues
        try {
            const dateParts = record['Date/Time Occurred'].split(' ')[0].split('/');
            if (dateParts.length !== 3) return;
            
            // Assume MM/DD/YYYY format
            const month = `${dateParts[2]}-${String(dateParts[0]).padStart(2, '0')}`;
            monthCounts[month] = (monthCounts[month] || 0) + 1;
        } catch (e) {
            console.warn("Error parsing date:", record['Date/Time Occurred']);
        }
    });

    let months = Object.keys(monthCounts).sort();
    if (startDate) {
        months = months.filter(month => month >= startDate);
    }
    if (endDate) {
        months = months.filter(month => month <= endDate);
    }

    // If no data, display a message
    if (months.length === 0) {
        displayNoDataMessage('reportsPerMonthChart', 'No monthly report data available for the selected filters');
        return;
    }

    const plotlyData = [{
        x: months,
        y: months.map(month => monthCounts[month] || 0),
        type: 'scatter',
        mode: 'lines+markers',
        marker: {
            color: 'rgba(55, 128, 191, 0.7)',
            size: 8
        },
        line: {
            color: 'rgba(55, 128, 191, 1.0)',
            width: 2
        }
    }];

    let title = "Reports Per Month";
    if (startDate || endDate) {
        title += "<br><sub>Date Range: ";
        title += startDate || "Start";
        title += " to ";
        title += endDate || "End";
        title += "</sub>";
    }
    
    const layout = {
        title: title,
        xaxis: {
            title: 'Month'
        },
        yaxis: {
            title: 'Number of Reports'
        },
        autosize: true
    };
    
    Plotly.newPlot('reportsPerMonthChart', plotlyData, layout, {responsive: true});
}


function createLocationHeatmap(data) {
    const locationCounts = {};
    data.forEach(record => {
        // Skip if location is missing
        if (!record['Location']) return;
        
        const location = record['Location'];
        locationCounts[location] = (locationCounts[location] || 0) + 1;
    });

    const plotData = Object.entries(locationCounts)
        .map(([location, count]) => ({ location, count }))
        .sort((a, b) => b.count - a.count)
        .slice(0, 15);
    
    // If no data, display a message
    if (plotData.length === 0) {
        displayNoDataMessage('locationHeatmapChart', 'No location data available');
        return;
    }
    
    const plotlyData = [{
        x: plotData.map(item => item.count),
        y: plotData.map(item => item.location),
        type: 'bar',
        orientation: 'h',
        marker: {
            color: 'rgba(55, 128, 191, 0.7)',
            line: {
                color: 'rgba(55, 128, 191, 1.0)',
                width: 1
            }
        }
    }];
    
    const layout = {
        title: 'Top 15 Crime Locations',
        xaxis: {
            title: 'Number of Reports',
            tickfont: {
                size: 10  
            }
        },
        yaxis: {
            title: 'Location',
            automargin: true,
            tickfont: {
                size: 9  
            }
        },
        font: {
            size: 11  
        },
        margin: {
            l: 150, 
            r: 30,
            t: 50,
            b: 70
        },
        height: 500, 
        width: 1200,  
        autosize: false
    };

    const config = {
        responsive: true,
        scrollZoom: true
    };
    
    Plotly.newPlot('locationHeatmapChart', plotlyData, layout, config);
}

function createDayOfWeekAnalysis(data) {
    const weekdayCounts = {
        'Sunday': 0,
        'Monday': 0,
        'Tuesday': 0,
        'Wednesday': 0,
        'Thursday': 0,
        'Friday': 0,
        'Saturday': 0
    };
    
    let hasValidDates = false;
    
    data.forEach(record => {
        // Skip if date is missing or invalid
        if (!record['Date/Time Occurred']) return;
        
        try {
            const dateStr = record['Date/Time Occurred'].split(' ')[0];
            const date = new Date(dateStr);
            
            if (isNaN(date.getTime())) return; // Skip invalid dates
            
            hasValidDates = true;
            const weekday = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'][date.getDay()];
            weekdayCounts[weekday]++;
        } catch (e) {
            console.warn("Error parsing date for day of week:", record['Date/Time Occurred']);
        }
    });

    // If no valid dates, display a message
    if (!hasValidDates) {
        displayNoDataMessage('dayOfWeekChart', 'No valid date data available for day of week analysis');
        return;
    }

    const weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
    
    const plotlyData = [{
        x: weekdays,
        y: weekdays.map(day => weekdayCounts[day]),
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
        title: 'Crime Reports by Day of the Week',
        xaxis: {
            title: 'Day of the Week'
        },
        yaxis: {
            title: 'Number of Reports'
        },
        autosize: true
    };
    
    Plotly.newPlot('dayOfWeekChart', plotlyData, layout, {responsive: true});
}


function createTimeAnalysis(data, crimeType) {
    // Filter by crime type if specified
    if (crimeType) {
        data = data.filter(record => record['Incident Type'] === crimeType);
    }

    const hourlyCounts = Array(24).fill(0);
    let validTimeCount = 0;
    
    data.forEach(record => {
        // Skip if date/time is missing or doesn't have time part
        if (!record['Date/Time Occurred']) return;
        
        const parts = record['Date/Time Occurred'].split(' ');
        if (parts.length < 2) return;
        
        try {
            const timeStr = parts[1];
            const hourPart = timeStr.split(':')[0];
            
            // Check for valid hour (0-23)
            if (hourPart && !isNaN(hourPart)) {
                const hour = parseInt(hourPart);
                if (hour >= 0 && hour < 24) {
                    hourlyCounts[hour]++;
                    validTimeCount++;
                }
            }
        } catch (e) {
            console.warn("Error parsing time:", record['Date/Time Occurred']);
        }
    });

    // If no valid times, display a message
    if (validTimeCount === 0) {
        displayNoDataMessage('timeAnalysisChart', 'No valid time data available for time analysis');
        return;
    }

    // Calculate days based on unique dates to avoid division by zero
    const uniqueDates = new Set();
    data.forEach(record => {
        if (record['Date/Time Occurred']) {
            const datePart = record['Date/Time Occurred'].split(' ')[0];
            if (datePart) uniqueDates.add(datePart);
        }
    });
    const numDays = Math.max(1, uniqueDates.size); // Ensure at least 1 to avoid division by zero
    
    const avgOccurrencesPerHour = hourlyCounts.map(count => (count / numDays).toFixed(2));

    const plotlyData = [{
        x: Array.from({length: 24}, (_, i) => i),
        y: avgOccurrencesPerHour,
        type: 'scatter',
        mode: 'lines+markers',
        marker: {
            color: 'rgba(55, 128, 191, 0.7)',
            size: 8
        },
        line: {
            color: 'rgba(55, 128, 191, 1.0)',
            width: 2
        }
    }];
    
    const layout = {
        title: 'Average Incidents Per Hour of the Day',
        xaxis: {
            title: 'Hour of the Day',
            tickmode: 'linear',
            dtick: 1
        },
        yaxis: {
            title: 'Average Incidents'
        },
        autosize: true
    };
    
    Plotly.newPlot('timeAnalysisChart', plotlyData, layout, {responsive: true});
}


function createIncidentStatusBreakdown(data) {
    const statusCounts = {};
    let hasValidStatus = false;
    
    data.forEach(record => {
        // Skip if disposition is missing
        if (!record['Disposition']) return;
        
        const status = record['Disposition'];
        statusCounts[status] = (statusCounts[status] || 0) + 1;
        hasValidStatus = true;
    });

    // If no valid status, display a message
    if (!hasValidStatus) {
        displayNoDataMessage('incidentStatusChart', 'No valid status data available');
        return;
    }

    const plotlyData = [{
        values: Object.values(statusCounts),
        labels: Object.keys(statusCounts),
        type: 'pie',
        hole: 0.4,
        marker: {
            colors: [
                'rgba(55, 128, 191, 0.7)',
                'rgba(50, 171, 96, 0.7)',
                'rgba(128, 0, 128, 0.7)',
                'rgba(219, 64, 82, 0.7)',
                'rgba(0, 128, 128, 0.7)',
                'rgba(128, 128, 0, 0.7)'
            ]
        }
    }];
    
    const layout = {
        title: 'Incident Status Breakdown',
        autosize: true
    };
    
    Plotly.newPlot('incidentStatusChart', plotlyData, layout, {responsive: true});
}


function createDollarAmountVisualization(data) {
    // Extract dollar amount incidents
    const dollarIncidents = data.filter(record => record['Incident Type'] && record['Incident Type'].includes('$'));
    
    if (dollarIncidents.length === 0) {
        displayNoDataMessage('dollarAmountChart', 'No dollar amount data available');
        return;
    }

    const theftData = [];
    
    dollarIncidents.forEach(record => {
        const incidentType = record['Incident Type'];
        // Improved regex to handle various dollar amount formats
        const matches = incidentType.match(/\$(\d+(?:,\d+)*(?:\.\d+)?)/);
        
        if (matches) {
            try {
                // Remove commas and convert to float
                const amountString = matches[1].replace(/,/g, '');
                const amount = parseFloat(amountString);
                
                if (!isNaN(amount)) {
                    theftData.push({
                        type: incidentType,
                        amount: amount
                    });
                }
            } catch (e) {
                console.warn("Error parsing dollar amount:", incidentType);
            }
        }
    });

    // If no valid theft data, display a message
    if (theftData.length === 0) {
        displayNoDataMessage('dollarAmountChart', 'No valid dollar amount data could be extracted');
        return;
    }

    const groupedData = {};
    theftData.forEach(item => {
        groupedData[item.type] = (groupedData[item.type] || 0) + item.amount;
    });

    const plotData = Object.entries(groupedData)
        .map(([type, amount]) => ({ type, amount }))
        .sort((a, b) => b.amount - a.amount);
    
    const plotlyData = [{
        x: plotData.map(item => item.type),
        y: plotData.map(item => item.amount),
        type: 'bar',
        marker: {
            color: plotData.map(item => item.amount),
            colorscale: 'Viridis'
        }
    }];
    
    const totalAmount = plotData.reduce((sum, item) => sum + item.amount, 0);
    
    const layout = {
        title: 'Total Dollar Amount Stolen by Incident Type',
        xaxis: {
            title: 'Incident Type',
            tickangle: -45,
            automargin: true,
            tickfont: {
                size: 9  
            }
        },
        yaxis: {
            title: 'Total Amount ($)',
            tickfont: {
                size: 10 
            }
        },
        font: {
            size: 11  
        },
        margin: {
            b: 150,
            l: 70,  
            r: 30, 
            t: 80   
        },
        height: 500,
        width: 1200, 
        autosize: false,
        annotations: [{
            x: 0.5,
            y: 1.05,
            xref: 'paper',
            yref: 'paper',
            text: `Approx. Total Amount Stolen: $${totalAmount.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`,
            showarrow: false,
            font: {
                size: 12, 
                color: 'black'
            },
            bgcolor: '#f8f9fa',
            bordercolor: '#343a40',
            borderwidth: 1,
            borderpad: 4
        }]
    };
    
    const config = {
        responsive: true,
        scrollZoom: true
    };
    
    Plotly.newPlot('dollarAmountChart', plotlyData, layout, config);
}
