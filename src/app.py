import streamlit as st
from .gemini_client import GeminiClient
from .config import SUPPORTED_FORMATS, MAX_FILE_SIZE_MB
import pandas as pd
import logging

# Configure logging
logger = logging.getLogger(__name__)

def main():
    st.title("FinState Analyzer")
    
    # Add API key configuration in sidebar
    api_key = st.sidebar.text_input(
        "Google API Key",
        type="password",
        help="Enter your Google API key"
    )
    
    if not api_key:
        st.warning("Please enter your Google API key to enable document recognition.")
        return

    st.sidebar.header("Document Upload")

    # Initialize client
    gemini_client = GeminiClient(api_key=api_key)

    # File upload section
    uploaded_files = st.sidebar.file_uploader(
        "Upload Financial Statements",
        type=SUPPORTED_FORMATS,
        accept_multiple_files=True,
        help=f"Supported formats: {', '.join(SUPPORTED_FORMATS)}. Max size: {MAX_FILE_SIZE_MB}MB"
    )

    if uploaded_files:
        for uploaded_file in uploaded_files:
            st.subheader(f"Processing: {uploaded_file.name}")
            process_and_display_results(uploaded_file, gemini_client)

def process_and_display_results(uploaded_file, gemini_client):
    """Process file and display results"""
    with st.spinner("Processing document..."):
        recognition_result = process_uploaded_file(uploaded_file, gemini_client)
        
        if recognition_result and recognition_result.success:
            display_results(recognition_result)
        else:
            st.error(f"Analysis failed: {recognition_result.error if recognition_result else 'Unknown error'}")

def process_uploaded_file(uploaded_file, gemini_client):
    """Process the uploaded file and return the recognition result"""
    try:
        mime_type = {
            'pdf': 'application/pdf',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png'
        }.get(uploaded_file.name.lower().split('.')[-1], 'application/octet-stream')

        return gemini_client.analyze_document(uploaded_file, mime_type)

    except Exception as e:
        logger.error(f"Error processing {uploaded_file.name}: {str(e)}")
        return None

def display_results(result):
    """Display the analysis results in a structured format"""
    # Display metadata
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Statement Type", result.statement_type)
    with col2:
        st.metric("Confidence Score", f"{result.confidence:.2%}")

    if result.extracted_data:
        tabs = st.tabs(["Financial Data", "Raw JSON", "Validation"])
        
        with tabs[0]:
            display_financial_data(result.extracted_data)
        with tabs[1]:
            st.json(result.extracted_data)
        with tabs[2]:
            display_validation_results(result.extracted_data)

def display_financial_data(data):
    """Display financial data in a structured format"""
    try:
        if "statements" not in data:
            st.error("No statements found in data")
            return

        # Display metadata first
        metadata = data.get("metadata", {})
        display_metadata(metadata)
        
        # Create tabs for each statement type
        statement_types = data["statements"].keys()
        tabs = st.tabs([type.replace('_', ' ').title() for type in statement_types])
        
        # Display each statement in its own tab
        for tab, statement_type in zip(tabs, statement_types):
            with tab:
                statement_data = data["statements"][statement_type]
                display_statement_data(statement_type, statement_data)

    except Exception as e:
        logger.error(f"Error displaying financial data: {str(e)}")
        st.error(f"Error displaying data: {str(e)}")

def display_statement_data(statement_type: str, data: dict):
    """Display statement data in a consistent format"""
    try:
        # Get years and create DataFrame structure
        years = sorted([year for year in data.keys() if year.isdigit()])
        if not years:
            st.warning("No yearly data found")
            return

        # Convert nested dictionary to flat format
        rows = []
        for key, value in flatten_dict(data[years[0]]).items():
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

def flatten_dict(d: dict, parent_key: str = '', sep: str = ' → ') -> dict:
    """Flatten nested dictionary with custom separator"""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

def display_styled_dataframe(df: pd.DataFrame, years: list):
    """Apply consistent styling to financial tables"""
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

def display_metadata(metadata: dict):
    """Display statement metadata"""
    if metadata:
        st.subheader("Statement Information")
        cols = st.columns(3)
        with cols[0]:
            st.metric("Currency", metadata.get("currency", "N/A"))
        with cols[1]:
            st.metric("Scale", metadata.get("scale", "N/A"))
        with cols[2]:
            st.metric("Unit", metadata.get("unit_symbol", "N/A"))

def display_validation_results(data):
    """Display validation checks and results"""
    st.subheader("Validation Checks")
    
    validations = [
        ("Statement Structure", "statements" in data),
        ("Metadata Present", "metadata" in data),
        ("Multi-year Data", len([k for k in data.get("statements", {}).get("profit_and_loss", {}) if k.isdigit()]) > 1)
    ]
    
    for check_name, check_result in validations:
        if check_result:
            st.success(f"✓ {check_name}")
        else:
            st.warning(f"⚠ {check_name}")

if __name__ == "__main__":
    main() 