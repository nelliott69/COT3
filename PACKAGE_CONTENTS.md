# COT Analyzer Package Contents

This package contains everything needed to run the COT Positions Analyzer application.

## Files Included

### Core Application
- `app.py` - Main Streamlit application with all functionality
- `.streamlit/config.toml` - Streamlit configuration for proper server setup

### Setup and Installation
- `setup.py` - Automated dependency installer
- `run.py` - Quick start script to launch the application
- `requirements_package.txt` - List of required Python packages

### Documentation
- `README.md` - Complete usage instructions and feature overview
- `PACKAGE_CONTENTS.md` - This file explaining package structure

## Quick Start

1. **Install dependencies**:
   ```bash
   python setup.py
   ```

2. **Run the application**:
   ```bash
   python run.py
   ```
   OR
   ```bash
   streamlit run app.py
   ```

3. **Access the app**: Opens automatically at http://localhost:8501

## Manual Installation (Alternative)

If the setup script doesn't work, you can install manually:

```bash
pip install streamlit pandas plotly requests numpy cot-reports
streamlit run app.py
```

## System Requirements

- Python 3.11 or higher
- Internet connection (for fetching CFTC data)
- Modern web browser
- ~50MB RAM for typical usage

## Package Features

- **Self-contained**: All code in single app.py file
- **Zero configuration**: Ready to run after dependency installation  
- **Professional design**: Dark theme charts with clean interface
- **Real CFTC data**: Direct integration with official data sources
- **Fast search**: Smart market filtering for quick analysis

The application will automatically fetch real COT data from the CFTC when you use it, so no sample data files are needed.