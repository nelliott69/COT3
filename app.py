import streamlit as st
import sys

# Check for required dependencies
missing_packages = []
try:
    import pandas as pd
except ImportError:
    missing_packages.append("pandas")

try:
    import plotly.express as px
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
except ImportError:
    missing_packages.append("plotly")

try:
    import requests
except ImportError:
    missing_packages.append("requests")

try:
    import numpy as np
except ImportError:
    missing_packages.append("numpy")

try:
    from cot_reports import cot_year
    COT_LIBRARY_AVAILABLE = True
except ImportError:
    COT_LIBRARY_AVAILABLE = False
    missing_packages.append("cot-reports")

# Display error if packages are missing
if missing_packages:
    st.error(f"""
    **Missing Required Packages**: {', '.join(missing_packages)}
    
    **To fix this, run:**
    ```
    pip install {' '.join(missing_packages)}
    ```
    
    **Or use the setup script:**
    ```
    python setup.py
    ```
    """)
    st.stop()

from io import StringIO
import csv
from datetime import datetime, timedelta
import re

# Configure page
st.set_page_config(
    page_title="COT Positions Analyzer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

def fetch_csv_data(url):
    """Fetch CSV data from Google Sheets URL"""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        # Parse CSV data
        data = list(csv.DictReader(StringIO(response.text)))
        
        if not data:
            st.error("No data found in the CSV file.")
            return None
            
        return pd.DataFrame(data)
        
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching data: {str(e)}")
        return None
    except Exception as e:
        st.error(f"Error parsing CSV data: {str(e)}")
        return None

def fetch_cftc_api_data(report_type='legacy_fut', max_records=5000):
    """Fetch COT data directly from CFTC API"""
    try:
        # CFTC API endpoints for different report types
        api_endpoints = {
            'legacy_fut': '6dca-aqww.json',  # Legacy Futures Only
            'legacy_combined': 'jun7-fc8e.json',  # Legacy Combined (Futures + Options)
            'disaggregated_fut': 'kh3c-gbw2.json',  # Disaggregated Futures Only
            'tff_fut': 'yw9f-hn96.json',  # Traders in Financial Futures
        }
        
        if report_type not in api_endpoints:
            st.error(f"Unknown report type: {report_type}")
            return None
        
        base_url = "https://publicreporting.cftc.gov/resource/"
        endpoint = api_endpoints[report_type]
        url = f"{base_url}{endpoint}"
        
        # Add parameters to limit results and get recent data
        params = {
            '$limit': max_records,
            '$order': 'report_date_as_yyyy_mm_dd DESC'
        }
        
        response = requests.get(url, params=params, timeout=60)
        response.raise_for_status()
        
        data = response.json()
        if not data:
            st.error("No data returned from CFTC API.")
            return None
        
        df = pd.DataFrame(data)
        
        # Convert date formats to match expected format  
        if 'report_date_as_yyyy_mm_dd' in df.columns:
            df['Report_Date_as_MM_DD_YYYY'] = pd.to_datetime(df['report_date_as_yyyy_mm_dd']).dt.strftime('%m/%d/%Y')
        elif 'Report_Date_as_YYYY_MM_DD' in df.columns:
            df['Report_Date_as_MM_DD_YYYY'] = pd.to_datetime(df['Report_Date_as_YYYY_MM_DD']).dt.strftime('%m/%d/%Y')
        
        # Standardize market names column
        if 'Market_and_Exchange_Names' not in df.columns and 'market_and_exchange_names' in df.columns:
            df['Market_and_Exchange_Names'] = df['market_and_exchange_names']
        
        return df
        
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching CFTC API data: {str(e)}")
        return None
    except Exception as e:
        st.error(f"Error processing CFTC data: {str(e)}")
        return None

def fetch_cftc_website_data():
    """Fetch COT data directly from CFTC Legacy Combined website"""
    try:
        # Direct CSV download from CFTC Legacy Combined dataset
        url = "https://publicreporting.cftc.gov/api/views/jun7-fc8e/rows.csv?accessType=DOWNLOAD"
        
        st.info("Fetching data from CFTC Legacy Combined dataset...")
        
        # Download the CSV data
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        
        # Parse CSV data
        csv_data = StringIO(response.text)
        df = pd.read_csv(csv_data)
        
        if df.empty:
            st.error("No data found in CFTC website response")
            return None
        
        # The CFTC website uses different column names, map them to standard format
        column_mapping = {
            'Report_Date_as_YYYY_MM_DD': 'Report_Date_as_YYYY_MM_DD',
            'Market_and_Exchange_Names': 'Market_and_Exchange_Names',
            'Comm_Positions_Long_All': 'Comm_Positions_Long_All',
            'Comm_Positions_Short_All': 'Comm_Positions_Short_All',
            'NonComm_Positions_Long_All': 'NonComm_Positions_Long_All',
            'NonComm_Positions_Short_All': 'NonComm_Positions_Short_All',
            'NonRept_Positions_Long_All': 'NonRept_Positions_Long_All',
            'NonRept_Positions_Short_All': 'NonRept_Positions_Short_All'
        }
        
        # Only rename columns that exist
        existing_mapping = {k: v for k, v in column_mapping.items() if k in df.columns}
        df = df.rename(columns=existing_mapping)
        
        # Convert date format from YYYY-MM-DD to MM/DD/YYYY
        if 'Report_Date_as_YYYY_MM_DD' in df.columns:
            df['Report_Date_as_MM_DD_YYYY'] = pd.to_datetime(df['Report_Date_as_YYYY_MM_DD']).dt.strftime('%m/%d/%Y')
        
        st.success(f"Successfully loaded {len(df)} records from CFTC website")
        return df
        
    except requests.exceptions.RequestException as e:
        st.error(f"Network error fetching CFTC website data: {str(e)}")
        return None
    except Exception as e:
        st.error(f"Error processing CFTC website data: {str(e)}")
        return None

def fetch_cot_library_data(year=None, report_type='legacy_fut'):
    """Fetch COT data using the cot_reports library"""
    if not COT_LIBRARY_AVAILABLE:
        st.error("COT library not available. Please install with: pip install cot-reports")
        return None
    
    try:
        if year is None:
            year = datetime.now().year
        
        # Map report types to library parameters
        library_report_types = {
            'legacy_fut': 'legacy_fut',
            'legacy_combined': 'legacy_futopt',
            'disaggregated_fut': 'disaggregated_fut', 
            'tff_fut': 'traders_in_financial_futures_fut'
        }
        
        lib_report_type = library_report_types.get(report_type, 'legacy_fut')
        
        df = cot_year(year=year, cot_report_type=lib_report_type)
        
        if df is None or df.empty:
            st.error(f"No COT data found for year {year}")
            return None
        
        # Map exact column names from the COT library output
        column_mapping = {
            'Market and Exchange Names': 'Market_and_Exchange_Names',
            'As of Date in Form YYYY-MM-DD': 'Report_Date_as_YYYY_MM_DD',
            'Commercial Positions-Long (All)': 'Comm_Positions_Long_All',
            'Commercial Positions-Short (All)': 'Comm_Positions_Short_All',
            'Noncommercial Positions-Long (All)': 'NonComm_Positions_Long_All',
            'Noncommercial Positions-Short (All)': 'NonComm_Positions_Short_All',
            'Nonreportable Positions-Long (All)': 'NonRept_Positions_Long_All',
            'Nonreportable Positions-Short (All)': 'NonRept_Positions_Short_All'
        }
        
        # Rename columns
        df = df.rename(columns=column_mapping)
        
        # Convert date format from YYYY-MM-DD to MM/DD/YYYY
        if 'Report_Date_as_YYYY_MM_DD' in df.columns:
            df['Report_Date_as_MM_DD_YYYY'] = pd.to_datetime(df['Report_Date_as_YYYY_MM_DD']).dt.strftime('%m/%d/%Y')
        
        return df
        
    except Exception as e:
        st.error(f"Error fetching COT library data: {str(e)}")
        st.error(f"Exception details: {type(e).__name__}: {str(e)}")
        return None

def clean_and_convert_data(df):
    """Clean and convert data types"""
    df_clean = df.copy()
    
    # Remove completely empty rows
    df_clean = df_clean.dropna(how='all')
    
    # Try to convert numeric columns
    for col in df_clean.columns:
        # Skip if column is already numeric
        if pd.api.types.is_numeric_dtype(df_clean[col]):
            continue
            
        # Try to convert to numeric
        try:
            # Remove common non-numeric characters
            cleaned_values = df_clean[col].astype(str).str.replace(',', '').str.replace('$', '').str.replace('%', '')
            numeric_series = pd.to_numeric(cleaned_values, errors='coerce')
            
            # If more than 50% of values are numeric, convert the column
            if numeric_series.count() / len(df_clean) > 0.5:
                df_clean[col] = numeric_series
        except:
            continue
    
    return df_clean

def get_column_types(df):
    """Categorize columns by data type"""
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    datetime_cols = df.select_dtypes(include=['datetime64']).columns.tolist()
    
    return numeric_cols, categorical_cols, datetime_cols

def create_summary_stats(df, numeric_cols):
    """Create summary statistics for numeric columns"""
    if not numeric_cols:
        return None
        
    stats_df = df[numeric_cols].describe().round(2)
    return stats_df

def create_bar_chart(df, x_col, y_col, title):
    """Create an interactive bar chart"""
    if df[x_col].dtype == 'object':
        # Group by categorical variable and aggregate
        grouped = df.groupby(x_col)[y_col].sum().reset_index()
        fig = px.bar(grouped, x=x_col, y=y_col, title=title)
    else:
        fig = px.bar(df, x=x_col, y=y_col, title=title)
    
    fig.update_layout(xaxis_tickangle=-45)
    return fig

def create_line_chart(df, x_col, y_col, title):
    """Create an interactive line chart"""
    # Sort by x column for proper line connection
    df_sorted = df.sort_values(x_col)
    fig = px.line(df_sorted, x=x_col, y=y_col, title=title, markers=True)
    return fig

def create_scatter_plot(df, x_col, y_col, color_col, title):
    """Create an interactive scatter plot"""
    fig = px.scatter(df, x=x_col, y=y_col, color=color_col, title=title, hover_data=df.columns)
    return fig

def create_pie_chart(df, values_col, names_col, title):
    """Create an interactive pie chart"""
    # Group by names column and sum values
    grouped = df.groupby(names_col)[values_col].sum().reset_index()
    fig = px.pie(grouped, values=values_col, names=names_col, title=title)
    return fig

def create_histogram(df, col, title):
    """Create a histogram for numeric data"""
    fig = px.histogram(df, x=col, title=title, nbins=30)
    return fig

def create_cot_positions_chart(df, market_name):
    """Create Commitment of Traders positions chart for specific market"""
    # Filter data for the selected market
    market_data = df[df['Market_and_Exchange_Names'] == market_name].copy()
    
    if market_data.empty:
        return None
    
    # Use the specific date column
    date_col = 'Report_Date_as_MM_DD_YYYY'
    if date_col not in market_data.columns:
        st.error(f"Date column '{date_col}' not found in data")
        return None
    
    # Convert date column to datetime and sort
    try:
        market_data[date_col] = pd.to_datetime(market_data[date_col], format='%m/%d/%Y')
        market_data = market_data.sort_values(date_col)
    except:
        try:
            market_data[date_col] = pd.to_datetime(market_data[date_col])
            market_data = market_data.sort_values(date_col)
        except:
            st.warning("Could not parse date column, using as-is")
    
    # Calculate net positions
    required_cols = [
        'Comm_Positions_Long_All', 'Comm_Positions_Short_All',
        'NonComm_Positions_Long_All', 'NonComm_Positions_Short_All',
        'NonRept_Positions_Long_All', 'NonRept_Positions_Short_All'
    ]
    
    # Check if all required columns exist
    missing_cols = [col for col in required_cols if col not in market_data.columns]
    if missing_cols:
        st.error(f"Missing required columns: {missing_cols}")
        return None
    
    # Convert to numeric if not already
    for col in required_cols:
        market_data[col] = pd.to_numeric(market_data[col], errors='coerce')
    
    # Calculate net positions
    market_data['Commercial_Net'] = market_data['Comm_Positions_Long_All'] - market_data['Comm_Positions_Short_All']
    market_data['NonCommercial_Net'] = market_data['NonComm_Positions_Long_All'] - market_data['NonComm_Positions_Short_All']
    market_data['NonReportable_Net'] = market_data['NonRept_Positions_Long_All'] - market_data['NonRept_Positions_Short_All']
    
    # Create the chart
    fig = go.Figure()
    
    # Add bars for each position type
    fig.add_trace(
        go.Bar(
            x=market_data[date_col],
            y=market_data['Commercial_Net'],
            name='Commercials',
            marker_color='rgba(255, 0, 0, 0.7)',
            width=pd.Timedelta(days=5).total_seconds() * 1000 if len(market_data) > 1 else None
        )
    )
    
    fig.add_trace(
        go.Bar(
            x=market_data[date_col],
            y=market_data['NonCommercial_Net'],
            name='Large_Speculators',
            marker_color='rgba(0, 0, 255, 0.7)',
            width=pd.Timedelta(days=5).total_seconds() * 1000 if len(market_data) > 1 else None
        )
    )
    
    fig.add_trace(
        go.Bar(
            x=market_data[date_col],
            y=market_data['NonReportable_Net'],
            name='Small_Speculators',
            marker_color='rgba(255, 255, 0, 0.7)',
            width=pd.Timedelta(days=5).total_seconds() * 1000 if len(market_data) > 1 else None
        )
    )
    
    # Add zero line
    fig.add_hline(y=0, line_dash="solid", line_color="white", line_width=1)
    
    # Update layout for dark theme similar to reference
    fig.update_layout(
        title=dict(
            text=f"{market_name}",
            x=0.5,
            xanchor='center',
            font=dict(size=16, color='white')
        ),
        plot_bgcolor='rgba(0,0,0,0.9)',
        paper_bgcolor='rgba(0,0,0,0.9)',
        font=dict(color='white'),
        barmode='overlay',
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.3,
            xanchor="center",
            x=0.5,
            bgcolor='rgba(0,0,0,0.5)',
            font=dict(color='white')
        ),
        xaxis=dict(
            title='Date',
            gridcolor='rgba(128,128,128,0.3)',
            tickformat='%m/%d/%y',
            tickangle=45
        ),
        yaxis=dict(
            title='Net Positions',
            gridcolor='rgba(128,128,128,0.3)',
            zeroline=True,
            zerolinecolor='white',
            zerolinewidth=1
        ),
        height=600,
        margin=dict(b=100)
    )
    
    return fig

def main():
    pass  # Removed title section
    
    # Default CSV URL
    default_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSlve_l2yUdQGkF1K0xUdqqrhqBGFxMa3y6wea8TKNgXAcYynJxJujS4n78Z7pSwbzr6huXXOSUc3i-/pub?gid=0&single=true&output=csv"
    
    # Sidebar for configuration
    st.sidebar.header("📊 COT Data Source")
    
    # Simplified data source - only CFTC Fetch
    st.sidebar.markdown("**Automatic CFTC Data Fetching**")
    
    # Report type selection
    report_type = st.sidebar.selectbox(
            "Report Type:",
            ["legacy_fut", "legacy_combined", "disaggregated_fut", "tff_fut"],
            format_func=lambda x: {
                "legacy_fut": "Legacy Futures Only (1986-Present)",
                "legacy_combined": "Legacy Combined - Futures + Options (1986-Present)",
                "disaggregated_fut": "Disaggregated Futures (2009-Present)", 
                "tff_fut": "Financial Futures (2009-Present)"
            }[x],
            help="Choose the type of COT report to fetch"
    )
    
    # Year selection for COT Library
    year = st.sidebar.selectbox(
        "Year:",
        list(range(datetime.now().year, 1985, -1)),
        help="Select year for COT data"
    )
        
    load_data = st.sidebar.button("Load Data", type="primary")
    
    # Show data update info
    st.sidebar.info("📅 COT data updates every Friday at 3:30 PM ET with Tuesday's positions")
    
    # Initialize session state
    if 'data' not in st.session_state:
        st.session_state.data = None
    
    # Load data using COT Library
    if load_data:
        with st.spinner(f"Fetching {year} {report_type} data using COT library..."):
            raw_data = fetch_cot_library_data(year, report_type)
            if raw_data is not None:
                st.session_state.data = clean_and_convert_data(raw_data)
                st.success(f"COT library for {year}")
    
    # Auto-load demo data if no data is present
    elif st.session_state.data is None:
        st.info("Loading demo data automatically...")
        if COT_LIBRARY_AVAILABLE:
            with st.spinner("Loading 2024 legacy futures data..."):
                raw_data = fetch_cot_library_data(2024, 'legacy_fut')
                if raw_data is not None:
                    st.session_state.data = clean_and_convert_data(raw_data)
                    st.success(f"COT library for {2024}")
        else:
            st.warning("COT library not available for demo data. Please use the data loading options in the sidebar.")
    
    # Main content
    if st.session_state.data is not None:
        df = st.session_state.data
        numeric_cols, categorical_cols, datetime_cols = get_column_types(df)
        
        filtered_df = df.copy()
        
        # Check if this is COT data
        is_cot_data = 'Market_and_Exchange_Names' in df.columns and any(
            col in df.columns for col in [
                'Comm_Positions_Long_All', 'Comm_Positions_Short_All',
                'NonComm_Positions_Long_All', 'NonComm_Positions_Short_All',
                'NonRept_Positions_Long_All', 'NonRept_Positions_Short_All'
            ]
        )
        
        if is_cot_data:
            # Market selection section
            
            # Market selection with search functionality
            markets = sorted(df['Market_and_Exchange_Names'].dropna().unique())
            
            # Add search functionality
            col1, col2 = st.columns([3, 1])
            
            with col1:
                search_term = st.text_input(
                    "🔍 Search Markets:",
                    placeholder="Type to search (e.g., CRUDE, WHEAT, GOLD)...",
                    help="Enter keywords to filter the market list"
                )
            
            with col2:
                st.markdown("<br>", unsafe_allow_html=True)  # Add spacing
                if st.button("Clear", help="Clear search and show all markets"):
                    search_term = ""
            
            # Filter markets based on search
            if search_term:
                filtered_markets = [m for m in markets if search_term.upper() in m.upper()]
                if not filtered_markets:
                    st.warning(f"No markets found containing '{search_term}'. Showing all markets.")
                    filtered_markets = markets
            else:
                filtered_markets = markets
            
            # Market dropdown with filtered results
            selected_market = st.selectbox(
                f"Select Market ({len(filtered_markets)} markets):",
                filtered_markets,
                help="Choose a market to view net positions (Long - Short) for each trader category"
            )
            
            if selected_market:
                cot_fig = create_cot_positions_chart(filtered_df, selected_market)
                if cot_fig:
                    st.plotly_chart(cot_fig, use_container_width=True)
                    
                    # Show explanation
                    with st.expander("📖 Chart Explanation"):
                        st.markdown("""
                        **Chart Elements:**
                        - 🔴 **Red Bars (Commercials)**: Net positions of commercial traders/hedgers
                        - 🔵 **Blue Bars (Large Speculators)**: Net positions of large non-commercial traders  
                        - 🟡 **Yellow Bars (Small Speculators)**: Net positions of small/non-reportable traders
                        
                        **Net Position Calculation**: Long positions minus Short positions
                        - Positive values = More long than short positions (bullish sentiment)
                        - Negative values = More short than long positions (bearish sentiment)
                        - White zero line = Reference point for net positions
                        
                        **Chart Style**: Dark theme with overlaid bars similar to professional trading platforms
                        """)
                else:
                    st.error("Could not create chart for the selected market. Please check the data.")
            

        
    else:
        st.info("👆 Please load data using the sidebar to begin visualization.")
        
        # Show data source info
        st.header("📊 COT Data Analyzer")
        st.markdown("""
        **Streamlined COT Analysis with Automatic Data Fetching**
        
        **Features:**
        - 🚀 **Automatic CFTC Data Fetching** - No manual work required
        - 🔍 **Smart Market Search** - Quickly find any commodity or market
        - 📊 **Multiple Report Types** - Legacy, Disaggregated, and Financial Futures
        - 📈 **Interactive Charts** - Professional dark theme visualizations
        - 📅 **Historical Data** - Access to complete CFTC database
        
        **Available Reports:**
        - **Legacy Futures Only** (1986-Present) - Classic COT format
        - **Legacy Combined** - Futures + Options (1986-Present) 
        - **Disaggregated Futures** (2009-Present) - Producer/Swap/Money Manager breakdown
        - **Financial Futures** (2009-Present) - Asset Manager/Leveraged Funds detail
        
        **How to Use:**
        1. Select report type and fetch method in the sidebar
        2. Click "Fetch CFTC Data" to load the latest data
        3. Use the search box to quickly find your market
        4. View net positions with professional trading charts
        """)
        
        st.info("💡 **Tip:** Use the search function to quickly find markets like 'CRUDE', 'WHEAT', 'GOLD', 'BITCOIN', etc.")

if __name__ == "__main__":
    main()
