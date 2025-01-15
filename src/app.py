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
    
    # Initialize session state for processed results
    if 'processed_results' not in st.session_state:
        st.session_state.processed_results = None
    
    # Add API key configuration in sidebar
    api_key = st.sidebar.text_input(
        "Google API Key",
        type="password",
        help="Enter your Google API key",
        value=os.getenv('GEMINI_API_KEY','')
    )
    
    if not api_key:
        st.warning("Please enter your Google API key to enable document recognition.")
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
                        downloaded_files = downloader.download_all_accounts()
                        
                        # Convert downloaded files to BytesIO objects
                        uploaded_files = []  # Reset the list before adding new files
                        for filepath in downloaded_files:
                            with open(filepath, 'rb') as f:
                                file_bytes = f.read()
                                filename = os.path.basename(filepath)
                                file_obj = BytesIO(file_bytes)
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
                        
                        # Display processing summary
                        if processed_files:
                            st.success(f"Successfully processed: {', '.join(processed_files)}")
                        
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
            display_consolidated_results(st.session_state.processed_results)

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
    """Display both tabular data and raw JSON with export functionality"""
    try:
        if "statements" not in data:
            st.error("No statements found in data")
            return

        # Create main tabs for Tables and Raw JSON
        tab_tables, tab_json = st.tabs(["Financial Statements", "Raw JSON"])
        
        with tab_tables:
            # Display metadata
            metadata = data.get("metadata", {})
            display_metadata(metadata)
            
            # Create tabs for each statement type
            statement_types = [st for st, sd in data["statements"].items() if sd]
            if statement_types:
                tabs = st.tabs([type.replace('_', ' ').title() for type in statement_types])
                
                # Display each statement in its own tab
                for tab, statement_type in zip(tabs, statement_types):
                    with tab:
                        statement_data = data["statements"][statement_type]
                        display_statement_data(statement_type, statement_data)
            else:
                st.warning("No statement data found")
        
        with tab_json:
            # Add export options
            col1, col2 = st.columns([3, 1])
            with col1:
                st.json(data)  # Display formatted JSON
            with col2:
                # Store JSON string in session state to avoid reprocessing
                if 'json_data' not in st.session_state:
                    st.session_state.json_data = json.dumps(data, indent=2)
                
                # Download button
                st.download_button(
                    label="💾 Download JSON",
                    data=st.session_state.json_data,
                    file_name="financial_statements.json",
                    mime="application/json",
                    help="Download the financial statements as a JSON file",
                    use_container_width=True
                )
                
                # Copy to clipboard button
                st.button(
                    "📋 Copy JSON",
                    help="Copy the JSON to clipboard",
                    use_container_width=True,
                    on_click=lambda: st.write(
                        f'<script>navigator.clipboard.writeText({json.dumps(st.session_state.json_data)})</script>',
                        unsafe_allow_html=True
                    )
                )

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
            st.subheader("Statement Information")
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

if __name__ == "__main__":
    main() 