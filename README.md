# GBIF API Client with Shiny Frontend

This project provides a Python API interface for the GBIF (Global Biodiversity Information Facility) API using the pygbif library, and a Shiny for Python frontend for interactive exploration of biodiversity data.

## Features

- API client using pygbif for accessing GBIF data
- **Dashboard-style interface**: Modern, card-based layout with organized sections
- Shiny web app for searching species, occurrences, and visualizing data
- **Modern UI theme**: Clean Bootswatch Cosmo theme for better user experience
- Interactive maps and charts
- **Enhanced Size Data Detection**: Now checks MeasurementOrFact extensions for detailed morphological measurements (cell size, biovolume, biomass, etc.)
- **Bulk species analysis**: Upload Excel file with species list and check which species have size data available in GBIF
- **Real-time progress tracking**: Monitor bulk analysis progress with visual indicators and cancellation option

## Installation

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run the Shiny app: `shiny run app.py`

## Usage

The dashboard provides an intuitive interface for exploring biodiversity data:

### **Left Sidebar Controls**
- **Species Search Section**: Search for species, filter by country, and toggle size data filtering
- **Bulk Analysis Section**: Upload Excel files and control bulk species analysis

### **Main Dashboard Tabs**
- **📋 Species**: View species search results in a clean table format
- **📍 Occurrences**: Browse occurrence records with integrated statistics panel
- **🗺️ Map**: Interactive distribution maps powered by Plotly
- **📈 Bulk Analysis**: Results from bulk species analysis
- **⚡ Progress**: Real-time progress tracking for long-running analyses

The Shiny app allows users to:
- Search for species by name
- View occurrence records with size and trait data
- Visualize distributions on interactive maps
- Filter data by country and size availability
- Perform bulk analysis on multiple species from Excel files
- Monitor analysis progress in real-time
- **Bulk Analysis**: Upload an Excel file (.xlsx) with species names in the first column of the first sheet, then click "Analyze Species for Size Data" to check which species have organism size information available

## Bulk Analysis Feature

1. Prepare an Excel file with species names in the first column (no headers needed)
2. Upload the file using the file input in the sidebar
3. Click "Analyze Species for Size Data"
4. **Monitor Progress**: Switch to the "Progress" tab to see real-time updates including:
   - Current species being processed
   - Progress bar showing completion percentage
   - Number of species completed vs total
   - Status messages
5. **Cancel if needed**: Use the "Cancel Analysis" button to stop processing
6. View results in the "Bulk Analysis" tab showing:
   - Original species name
   - GBIF scientific name match
   - Total number of occurrences
   - Whether size data is available

## Enhanced Size Data Detection

The app now provides comprehensive size data detection by checking multiple sources:

### **MeasurementOrFact Extension**
- **Cell dimensions**: length, width, diameter, height
- **Volume measurements**: biovolume, biomass, carbon content
- **Size fractions**: mesh sizes, size classes from sampling protocols
- **Units**: micrometers (μm), cubic micrometers (μm³), picograms carbon (pg C cell⁻¹)

### **Data Sources Checked**
1. **MeasurementOrFact extension**: Detailed quantitative measurements
2. **Dynamic properties**: Morphological and trait data
3. **Sampling protocols**: Size fraction information (e.g., "20-200 μm mesh")
4. **Traditional fields**: organismQuantity, individualCount, sampleSizeValue

### **Recommended Datasets**
Some GBIF datasets are particularly rich in size data:
- **KPLANK**: Finnish Baltic Sea Monitoring (>240,000 records with size classes)
- **San Francisco Bay Phytoplankton**: Microscopic cell size analyses
- **Tara Oceans**: Size fraction data (20-200 μm range)
- **Inner Oslofjorden Phytoplankton**: Quantitative cell counts and biometrics

### **Size Data Types**
- **Specific measurements**: Exact cell dimensions (e.g., "42 μm long")
- **Size fractions**: Sampling ranges (e.g., ">20 μm mesh net")
- **Size classes**: Categorical size groupings