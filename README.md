# COT Positions Analyzer

A streamlined Streamlit web application for analyzing Commitment of Traders (COT) data with automated data fetching and intelligent market search capabilities.

## Features

- **Automatic CFTC Data Fetching**: Direct integration with CFTC's COT reports library
- **Smart Market Search**: Quickly filter and find specific commodities or markets
- **Multiple Report Types**: Support for Legacy, Disaggregated, and Financial Futures reports
- **Professional Visualizations**: Dark theme charts with net position analysis
- **Minimal Interface**: Clean, focused design for efficient trading analysis

## Installation

### Prerequisites

- Python 3.11 or higher
- pip package manager

### Setup

1. **Extract the package**
   ```bash
   unzip cot-analyzer-YYYYMMDD.zip
   cd cot-analyzer/
   ```

2. **One-Click Launch (Recommended)**
   ```bash
   python launch.py
   ```
   This automatically installs dependencies and runs the app.

3. **Alternative: Separate Steps**
   ```bash
   python setup.py    # Install dependencies
   python run.py      # Run the app
   ```

4. **Open your browser**
   - The app will automatically open at `http://localhost:8501`
   - Or manually navigate to the URL shown in the terminal

### Manual Installation (Alternative)

If the setup script doesn't work:

```bash
pip install streamlit pandas plotly requests numpy cot-reports
streamlit run app.py
```

### Troubleshooting

**Import Errors**: If you see "ModuleNotFoundError", run the setup script:
```bash
python setup.py
```

**Python Version**: Requires Python 3.8 or higher. Check with:
```bash
python --version
```

## Usage

1. **Select Report Type**: Choose from Legacy Futures, Combined, Disaggregated, or Financial Futures
2. **Choose Year**: Select the year for historical COT data (1986-present depending on report type)
3. **Load Data**: Click the "Load Data" button to fetch CFTC data
4. **Search Markets**: Use the search box to quickly find specific commodities (e.g., "CRUDE", "WHEAT", "GOLD")
5. **Analyze Positions**: View net positions with color-coded bars:
   - **Red**: Commercial traders (hedgers)
   - **Blue**: Large speculators (non-commercial)
   - **Yellow**: Small speculators (non-reportable)

## Chart Interpretation

- **Positive Values**: More long than short positions (bullish sentiment)
- **Negative Values**: More short than long positions (bearish sentiment)
- **White Zero Line**: Reference point for net position calculations

## Report Types Available

- **Legacy Futures Only** (1986-Present): Classic COT format
- **Legacy Combined** (1986-Present): Futures + Options data
- **Disaggregated Futures** (2009-Present): Producer/Swap/Money Manager breakdown
- **Financial Futures** (2009-Present): Asset Manager/Leveraged Funds detail

## Data Source

Data is automatically fetched from the CFTC (Commodity Futures Trading Commission) using the official COT reports library. The data updates every Friday at 3:30 PM ET with Tuesday's positions.

## Technical Requirements

- Internet connection for data fetching
- Modern web browser
- Approximately 50MB of RAM for typical usage

## License

This project is provided as-is for educational and analysis purposes.

## Support

For technical issues or questions about COT data interpretation, please refer to the CFTC's official documentation at https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm