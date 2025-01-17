import streamlit as st
from .gemini_client import GeminiClient, RecognitionResult
from .config import SUPPORTED_FORMATS, MAX_FILE_SIZE_MB
import pandas as pd
import logging
import json
import sys
import os
from .download_accounts import CompaniesHouseDownloader
from io import BytesIO
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List

# Configure logging to output to both file and console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),  # Print to terminal
        logging.FileHandler('app.log')      # Save to file
    ]
)

# Get logger
logger = logging.getLogger(__name__)

def main():
    logger.info("Starting FinState Analyzer")
    
    st.title("FinState Analyzer")
    
    # Initialize session state for processed results and company details
    if 'processed_results' not in st.session_state:
        st.session_state.processed_results = None
    if 'company_details' not in st.session_state:
        st.session_state.company_details = None
    
    # Add API key configuration in sidebar
    api_key = st.sidebar.text_input(
        "Google API Key",
        type="password",
        help="Enter your Google API key",
        value=os.getenv('GEMINI_API_KEY','')
    )

    if not api_key:
        st.warning("Please enter your Google API key to process documents.")
        return

    st.sidebar.header("Document Upload")

    # Initialize uploaded_files
    uploaded_files = []

    # Add Companies House input option
    use_companies_house = st.sidebar.checkbox("Download from Companies House")
    
    if use_companies_house:
        company_number = st.sidebar.text_input(
            "Companies House Number",
            help="Enter the 8-digit company registration number"
        )
        
        if st.sidebar.button("Download Accounts"):
            if not company_number:
                st.sidebar.error("Please enter a company number")
            else:
                with st.spinner("Downloading accounts from Companies House..."):
                    try:
                        downloader = CompaniesHouseDownloader(company_number)
                        
                        # Get company details and downloaded files in one go
                        company_details = downloader.get_company_details()
                        downloaded_files = downloader.download_all_accounts()
                        
                        # Set both the company details and prepare the files
                        st.session_state.company_details = company_details
                        
                        # Convert downloaded files to BytesIO objects
                        uploaded_files = []  # Reset the list before adding new files
                        for filename, content in downloaded_files:
                            file_obj = BytesIO(content)
                            # Add attributes to match Streamlit's UploadedFile
                            file_obj.name = filename
                            file_obj.type = "application/pdf"
                            uploaded_files.append(file_obj)
                        
                        st.sidebar.success(f"Downloaded {len(downloaded_files)} files")
                            
                    except Exception as e:
                        st.sidebar.error(f"Error downloading files: {str(e)}")
                        uploaded_files = []
    else:
        # Original file upload section
        uploaded_files = st.sidebar.file_uploader(
            "Upload Financial Statements",
            type=SUPPORTED_FORMATS,
            accept_multiple_files=True,
            help=f"Supported formats: {', '.join(SUPPORTED_FORMATS)}. Max size: {MAX_FILE_SIZE_MB}MB"
        )

    if uploaded_files:
        # Only process if we haven't already or if files changed
        current_files = [f.name for f in uploaded_files]
        if (st.session_state.processed_results is None or 
            'last_processed_files' not in st.session_state or 
            st.session_state.last_processed_files != current_files):
            
            try:
                # Process files
                gemini_client = GeminiClient(api_key=api_key)
                
                if len(uploaded_files) == 1:
                    # Single file processing logic
                    with st.spinner(f"Processing {uploaded_files[0].name}..."):
                        recognition_result = process_uploaded_file(uploaded_files[0], gemini_client)
                        if recognition_result is None:
                            st.error(f"Failed to process {uploaded_files[0].name}")
                            return
                        if recognition_result.success:
                            st.session_state.processed_results = recognition_result.extracted_data
                            st.session_state.last_processed_files = current_files
                        else:
                            st.error(f"Analysis failed: {recognition_result.error}")
                
                else:
                    # Multiple files processing logic
                    processed_files = []
                    failed_files = []
                    
                    for idx, uploaded_file in enumerate(uploaded_files):
                        with st.spinner(f"Processing: {uploaded_file.name}"):
                            recognition_result = process_uploaded_file(uploaded_file, gemini_client)
                            if recognition_result is None or not recognition_result.success:
                                failed_files.append((uploaded_file.name, recognition_result.error if recognition_result else "Processing failed"))
                                logger.warning(f"Failed to process {uploaded_file.name}")
                                continue
                            processed_files.append(uploaded_file.name)

                    if not processed_files:
                        st.error("No files were successfully processed")
                        return

                    # Consolidate results only for multiple files
                    with st.spinner("Consolidating statements..."):
                        consolidated_result = gemini_client.consolidate_statements()
                        
                        # Only show failed files if any
                        if failed_files:
                            st.warning("The following files had issues:")
                            for file_name, error in failed_files:
                                st.warning(f"- {file_name}: {error}")
                        
                        if consolidated_result.success:
                            st.session_state.processed_results = consolidated_result.extracted_data
                            st.session_state.last_processed_files = current_files
            
            except Exception as e:
                logger.error(f"Error in main processing: {str(e)}")
                st.error(f"Error processing files: {str(e)}")
        
        # Display results if available
        if st.session_state.processed_results:
            
            # Create tabs for tables and visualization
            tab_tables, tab_viz, tab_json = st.tabs(["Financial Statements", "Visualization", "Raw JSON"])
            
            with tab_tables:
                display_company_details()
                # Display metadata
                metadata = st.session_state.processed_results.get("metadata", {})
                display_metadata(metadata)
                
                # Create tabs for each statement type
                statement_types = [st for st, sd in st.session_state.processed_results["statements"].items() if sd]
                if statement_types:
                    tabs = st.tabs([type.replace('_', ' ').title() for type in statement_types])
                    
                    # Display each statement in its own tab
                    for tab, statement_type in zip(tabs, statement_types):
                        with tab:
                            statement_data = st.session_state.processed_results["statements"][statement_type]
                            display_statement_data(statement_type, statement_data)
                else:
                    st.warning("No statement data found")
            
            with tab_viz:
                display_visualizations(st.session_state.processed_results)
            
            with tab_json:
                # Add export options with unique keys
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.json(st.session_state.processed_results)
                with col2:
                    if 'json_data' not in st.session_state:
                        st.session_state.json_data = json.dumps(st.session_state.processed_results, indent=2)
                    
                    st.download_button(
                        label="💾 Download JSON",
                        data=st.session_state.json_data,
                        file_name="financial_statements.json",
                        mime="application/json",
                        help="Download the financial statements as a JSON file",
                        use_container_width=True,
                        key="download_json_main"
                    )
                    
                    st.button(
                        "📋 Copy JSON",
                        help="Copy the JSON to clipboard",
                        use_container_width=True,
                        key="copy_json_main",
                        on_click=lambda: st.write(
                            f'<script>navigator.clipboard.writeText({json.dumps(st.session_state.json_data)})</script>',
                            unsafe_allow_html=True
                        )
                    )

def consolidate_data(consolidated_data: dict, new_data: dict):
    """Merge new statement data into consolidated data structure"""
    try:
        # Use first metadata encountered
        if not consolidated_data["metadata"]:
            consolidated_data["metadata"] = new_data.get("metadata")

        # Merge statements
        for statement_type, years_data in new_data.get("statements", {}).items():
            if statement_type not in consolidated_data["statements"]:
                consolidated_data["statements"][statement_type] = {}
            
            # Add years data
            consolidated_data["statements"][statement_type].update(years_data)
    except Exception as e:
        logger.error(f"Error consolidating data: {str(e)}")
        raise

def display_consolidated_results(data: dict):
    """Display statement data in tabular format"""
    try:
        if "statements" not in data:
            st.error("No statements found in data")
            return

        # Display each statement type's data
        statement_data = data["statements"][statement_type]
        display_statement_data(statement_type, statement_data)

    except Exception as e:
        logger.error(f"Error displaying results: {str(e)}")
        st.error(f"Error displaying results: {str(e)}")

def display_statement_data(statement_type: str, data: dict):
    try:
        # Get all years and sort them
        years = sorted([year for year in data.keys() if year.isdigit()])
        if not years:
            st.warning("No yearly data found")
            return

        # Convert nested dictionary to flat format
        all_keys = set()
        for year in years:
            all_keys.update(flatten_dict(data[year]).keys())

        # Create rows maintaining order from earliest year
        rows = []
        for key in sorted(all_keys):
            row = {"Line Item": key}
            for year in years:
                year_data = flatten_dict(data[year])
                row[year] = year_data.get(key)
            rows.append(row)

        # Create and display DataFrame
        df = pd.DataFrame(rows)
        display_styled_dataframe(df, years)
    except Exception as e:
        st.error(f"Error displaying {statement_type}: {str(e)}")

def display_styled_dataframe(df: pd.DataFrame, years: list):
    try:
        # Format numbers, handling None values
        def format_value(x):
            if pd.isna(x):
                return ''
            try:
                return '{:,.1f}'.format(float(x))
            except (ValueError, TypeError):
                return str(x)

        # Style negative numbers in red
        def style_negative(x):
            try:
                return 'color: red' if float(x) < 0 else ''
            except (ValueError, TypeError):
                return ''

        # Apply styling
        styled_df = df.style\
            .format(format_value, subset=years)\
            .map(style_negative, subset=years)\
            .set_properties(**{
                'text-align': 'left',
                'font-family': 'monospace',
                'white-space': 'pre'
            })
        
        st.dataframe(styled_df, use_container_width=True)
    except Exception as e:
        st.error(f"Error styling dataframe: {str(e)}")

def display_metadata(metadata: dict):
    try:
        if metadata:
            cols = st.columns(3)
            with cols[0]:
                st.metric("Currency", metadata.get("currency", "N/A"))
            with cols[1]:
                st.metric("Scale", metadata.get("scale", "N/A"))
            with cols[2]:
                st.metric("Unit", metadata.get("unit_symbol", "N/A"))
    except Exception as e:
        st.error(f"Error displaying metadata: {str(e)}")

def flatten_dict(d: dict, parent_key: str = '', sep: str = ' → ') -> dict:
    try:
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)
    except Exception as e:
        logger.error(f"Error flattening dictionary: {str(e)}")
        return {}

def process_uploaded_file(uploaded_file, gemini_client):
    try:
        if not uploaded_file:
            logger.error("No file provided to process_uploaded_file")
            return RecognitionResult(success=False, error="No file provided")

        mime_type = {
            'pdf': 'application/pdf',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png'
        }.get(uploaded_file.name.lower().split('.')[-1])
        
        if not mime_type:
            logger.error(f"Unsupported file type: {uploaded_file.name}")
            return RecognitionResult(success=False, error=f"Unsupported file type: {uploaded_file.name}")

        logger.info(f"Processing file: {uploaded_file.name} with mime type: {mime_type}")
        recognition_result = gemini_client.analyze_document(uploaded_file, mime_type)
        return recognition_result

    except Exception as e:
        logger.error(f"Error processing {uploaded_file.name}: {str(e)}")
        return RecognitionResult(success=False, error=str(e))

def display_visualizations(data: dict):
    try:
        if not data or "statements" not in data:
            st.error("No statements found in data")
            return

        # Initialize selection state if not exists
        if 'selected_pl_metrics' not in st.session_state:
            st.session_state.selected_pl_metrics = [
                "Turnover", "Operating Profit", "Profit for the Financial Year"
            ]
        if 'selected_bs_metrics' not in st.session_state:
            st.session_state.selected_bs_metrics = [
                "Total Assets Less Current Liabilities", "Net Assets"
            ]

        statements = data.get("statements", {})
        
        # ROCE Analysis Section
        if "profit_and_loss" in statements and "balance_sheet" in statements:
            st.subheader("Return on Capital Employed (ROCE)")
            
            # Calculate ROCE for each year
            roce_data = {}
            for year in sorted(set(statements["profit_and_loss"].keys()) & set(statements["balance_sheet"].keys())):
                operating_profit = statements["profit_and_loss"][year].get("Operating Profit", 0)
                
                # Try to get Total Assets Less Current Liabilities directly
                capital_employed = statements["balance_sheet"][year].get("Total Assets Less Current Liabilities")
                
                # If not available, calculate it alternatively
                if not capital_employed:
                    total_assets = statements["balance_sheet"][year].get("Total Fixed Assets", 0) + \
                                 statements["balance_sheet"][year].get("Total Current Assets", 0)
                    current_liabilities = statements["balance_sheet"][year].get("Creditors: Amounts Falling Due Within One Year", 0)
                    capital_employed = total_assets + current_liabilities  # current_liabilities is typically negative
                
                if capital_employed:  # Avoid division by zero
                    roce_data[year] = (operating_profit / capital_employed) * 100
            
            if roce_data:
                # Calculate average ROCE
                avg_roce = sum(roce_data.values()) / len(roce_data)
                
                # Create ROCE bar chart
                fig_roce = go.Figure()
                
                # Add bars for yearly ROCE
                fig_roce.add_trace(go.Bar(
                    x=list(roce_data.keys()),
                    y=list(roce_data.values()),
                    name="Annual ROCE",
                    hovertemplate="Year: %{x}<br>ROCE: %{y:.1f}%<extra></extra>"
                ))
                
                # Add line for average ROCE
                fig_roce.add_trace(go.Scatter(
                    x=list(roce_data.keys()),
                    y=[avg_roce] * len(roce_data),
                    name="Long-term Average",
                    line=dict(color="red", dash="dash"),
                    hovertemplate="Long-term Average: %{y:.1f}%<extra></extra>"
                ))
                
                fig_roce.update_layout(
                    title="Return on Capital Employed by Year",
                    xaxis_title="Year",
                    yaxis_title="ROCE (%)",
                    hovermode='x unified',
                    showlegend=True,
                    height=400,
                    legend=dict(
                        yanchor="top",
                        y=0.99,
                        xanchor="left",
                        x=0.01
                    ),
                    xaxis=dict(
                        tickmode='linear',
                        dtick=1,
                        tickformat='d'
                    )
                )
                
                st.plotly_chart(fig_roce, use_container_width=True)

        # First section: Profit & Loss Metrics
        if "profit_and_loss" in statements:
            st.subheader("Profit & Loss Metrics")
            pl_data = statements["profit_and_loss"]
            
            years = sorted(pl_data.keys())
            if not years:
                st.warning("No P&L data available")
            else:
                metrics = list(pl_data[years[0]].keys())
                
                # Use session state for selections
                st.session_state.selected_pl_metrics = st.multiselect(
                    "Select P&L metrics to display",
                    metrics,
                    default=st.session_state.selected_pl_metrics,
                    key="pl_metrics_select"
                )
                
                if st.session_state.selected_pl_metrics:
                    fig_pl = go.Figure()
                    
                    for metric in st.session_state.selected_pl_metrics:
                        values = [pl_data[year].get(metric, 0) for year in years]
                        
                        fig_pl.add_trace(go.Scatter(
                            x=years,
                            y=values,
                            name=metric,
                            hovertemplate="%{fullData.name}<br>Year: %{x}<br>Value: £%{y:.1f}M<extra></extra>"
                        ))
                    
                    fig_pl.update_layout(
                        title="Profit & Loss Metrics Over Time",
                        xaxis_title="Year",
                        yaxis_title=f"Value ({data.get('metadata', {}).get('unit_symbol', '£M')})",
                        hovermode='x unified',
                        showlegend=True,
                        height=400,
                        legend=dict(
                            yanchor="top",
                            y=0.99,
                            xanchor="left",
                            x=0.01
                        ),
                        xaxis=dict(
                            tickmode='linear',
                            dtick=1,
                            tickformat='d'
                        )
                    )
                    
                    st.plotly_chart(fig_pl, use_container_width=True)

        # Second section: Balance Sheet Metrics
        if "balance_sheet" in statements:
            st.subheader("Balance Sheet Metrics")
            bs_data = statements["balance_sheet"]
            
            years = sorted(bs_data.keys())
            if not years:
                st.warning("No Balance Sheet data available")
            else:
                metrics = list(bs_data[years[0]].keys())
                
                # Use session state for selections
                st.session_state.selected_bs_metrics = st.multiselect(
                    "Select Balance Sheet metrics to display",
                    metrics,
                    default=st.session_state.selected_bs_metrics,
                    key="bs_metrics_select"
                )
                
                if st.session_state.selected_bs_metrics:
                    fig_bs = go.Figure()
                    
                    for metric in st.session_state.selected_bs_metrics:
                        values = [bs_data[year].get(metric, 0) for year in years]
                        
                        fig_bs.add_trace(go.Scatter(
                            x=years,
                            y=values,
                            name=metric,
                            hovertemplate="%{fullData.name}<br>Year: %{x}<br>Value: £%{y:.1f}M<extra></extra>"
                        ))
                    
                    fig_bs.update_layout(
                        title="Balance Sheet Metrics Over Time",
                        xaxis_title="Year",
                        yaxis_title=f"Value ({data.get('metadata', {}).get('unit_symbol', '£M')})",
                        hovermode='x unified',
                        showlegend=True,
                        height=400,
                        legend=dict(
                            yanchor="top",
                            y=0.99,
                            xanchor="left",
                            x=0.01
                        ),
                        xaxis=dict(
                            tickmode='linear',
                            dtick=1,
                            tickformat='d'
                        )
                    )
                    
                    st.plotly_chart(fig_bs, use_container_width=True)

    except Exception as e:
        logger.error(f"Error displaying visualizations: {str(e)}")
        st.error(f"Error displaying visualizations: {str(e)}")

def display_company_details():
    """Display company details if available in session state"""
    
    st.subheader("Statement Information")
    
    if st.session_state.company_details:
        st.header("Company Details")
        details = st.session_state.company_details
        st.write("**Name:**", details.get("name", "N/A"))
        st.write("**Number:**", details.get("number", "N/A"))

if __name__ == "__main__":
    main() 