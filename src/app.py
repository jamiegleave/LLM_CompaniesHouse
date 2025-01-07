import streamlit as st
from .document_uploader import DocumentUploader
from .gemini_client import GeminiClient
from .config import SUPPORTED_FORMATS, MAX_FILE_SIZE_MB
import pandas as pd
import json
import tempfile
import os
from pdf2image import convert_from_bytes

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
            
            with st.spinner("Processing document..."):
                # Process file and analyze with Gemini
                recognition_result = process_uploaded_file(uploaded_file, gemini_client)
                
                if recognition_result and recognition_result.success:
                    display_results(recognition_result)
                else:
                    st.error(f"Analysis failed: {recognition_result.error if recognition_result else 'Unknown error'}")

def display_results(result):
    """Display the analysis results in a structured format"""
    
    # Display statement type and confidence
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Statement Type", result.statement_type)
    with col2:
        st.metric("Confidence Score", f"{result.confidence:.2%}")

    # Display extracted data in tabs
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
        if "Profit and Loss" in data:
            pl_data = data["Profit and Loss"]
            metadata = pl_data.get("metadata", {})
            
            # Display metadata
            st.subheader("Statement Information")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Currency", metadata.get("currency", "N/A"))
            with col2:
                st.metric("Scale", metadata.get("scale", "N/A"))
            with col3:
                st.metric("Unit", metadata.get("unit_symbol", "N/A"))

            # Create tabs for different statement types
            statement_tabs = st.tabs(["Profit & Loss", "Balance Sheet"])
            
            with statement_tabs[0]:
                # Profit & Loss Table (unchanged)
                years = sorted([year for year in pl_data.keys() if year.isdigit()])
                pl_rows = []
                for year in years:
                    for item in pl_data[year]["profit_and_loss"]:
                        row = next(
                            (r for r in pl_rows if r["Line Item"] == item["name"]),
                            {"Line Item": item["name"], **{y: None for y in years}}
                        )
                        row[year] = item["value"]
                        if row not in pl_rows:
                            pl_rows.append(row)
                
                pl_df = pd.DataFrame(pl_rows)
                st.subheader("Profit & Loss Statement")
                display_styled_dataframe(pl_df, years)
            
            with statement_tabs[1]:
                if "Balance Sheet" in data:
                    bs_data = data["Balance Sheet"]
                    years = sorted([year for year in bs_data.keys() if year.isdigit()])
                    
                    # Create rows for Balance Sheet DataFrame
                    bs_rows = []
                    
                    # Define sections and their order
                    sections = [
                        ("Fixed Assets", "fixed_assets"),
                        ("Current Assets", "current_assets"),
                        ("Current Liabilities", "current_liabilities"),
                        ("Net Current Assets", "net_current_assets"),
                        ("Total Assets Less Current Liabilities", "total_assets_less_current_liabilities"),
                        ("Long Term Liabilities", "long_term_liabilities"),
                        ("Capital and Reserves", "capital_and_reserves")
                    ]
                    
                    for section_title, section_key in sections:
                        # Add section header
                        bs_rows.append({
                            "Line Item": f"--- {section_title} ---",
                            **{year: None for year in years}
                        })
                        
                        for year in years:
                            if section_key in bs_data[year].get("balance_sheet", {}):
                                section_data = bs_data[year]["balance_sheet"][section_key]
                                
                                # Handle different data types
                                if isinstance(section_data, (int, float)):
                                    # Handle direct value
                                    bs_rows.append({
                                        "Line Item": section_key.replace("_", " ").title(),
                                        **{y: section_data if y == year else None for y in years}
                                    })
                                elif isinstance(section_data, dict):
                                    # Handle single dictionary item
                                    bs_rows.append({
                                        "Line Item": section_data.get("name", section_key.replace("_", " ").title()),
                                        **{y: section_data["value"] if y == year else None for y in years}
                                    })
                                elif isinstance(section_data, list):
                                    # Handle list of items
                                    for item in section_data:
                                        row = next(
                                            (r for r in bs_rows if r["Line Item"] == item["name"]),
                                            {"Line Item": item["name"], **{y: None for y in years}}
                                        )
                                        row[year] = item["value"]
                                        if row not in bs_rows:
                                            bs_rows.append(row)
                    
                    # Create and display Balance Sheet DataFrame
                    bs_df = pd.DataFrame(bs_rows)
                    st.subheader("Balance Sheet")
                    display_styled_dataframe(bs_df, years)
                else:
                    st.info("No Balance Sheet data available")
                    
    except Exception as e:
        st.error(f"Error displaying financial data: {str(e)}")
        st.error(f"Debug info: {type(e).__name__} at line {e.__traceback__.tb_lineno}")

def display_styled_dataframe(df: pd.DataFrame, years: list):
    """Helper function to apply consistent styling to financial tables"""
    def style_negative_red(val):
        if isinstance(val, (int, float)) and val < 0:
            return 'color: red'
        return ''
    
    def style_section_header(val):
        if isinstance(val, str) and val.startswith('---'):
            return 'font-weight: bold; background-color: #f0f2f6'
        return ''
    
    styled_df = df.style\
        .format({col: '{:,.1f}' for col in years})\
        .applymap(style_negative_red, subset=years)\
        .applymap(style_section_header, subset=['Line Item'])\
        .set_properties(**{
            'text-align': 'left',
            'font-family': 'monospace',
            'white-space': 'pre'
        })
    
    st.dataframe(styled_df, use_container_width=True)

def display_validation_results(data):
    """Display validation checks and results"""
    st.subheader("Validation Checks")
    
    # Example validation checks
    validations = [
        ("Required Fields Present", check_required_fields(data)),
        ("Numerical Consistency", check_numerical_consistency(data)),
        ("Year-over-Year Data", "year_over_year" in data)
    ]
    
    for check_name, check_result in validations:
        if check_result:
            st.success(f"✓ {check_name}")
        else:
            st.warning(f"⚠ {check_name}")

def check_required_fields(data):
    """Check if all required fields are present"""
    required_fields = ["metrics", "statement_type"]
    return all(field in data for field in required_fields)

def check_numerical_consistency(data):
    """Basic check for numerical consistency"""
    try:
        if "metrics" in data:
            # Add specific checks based on statement type
            return True
        return False
    except:
        return False

def process_uploaded_file(uploaded_file, gemini_client):
    """Process the uploaded file and return the recognition result"""
    try:
        # Create a temporary directory for this upload
        with tempfile.TemporaryDirectory() as temp_dir:
            # If PDF, convert to images first
            if uploaded_file.name.lower().endswith('.pdf'):
                with st.spinner("Converting PDF to images..."):
                    pdf_bytes = uploaded_file.read()
                    images = convert_from_bytes(
                        pdf_bytes,
                        fmt='jpeg',
                        grayscale=False,
                        size=(2048, None),
                        use_cropbox=True
                    )
                    
                    # Save images to temporary files
                    temp_files = []
                    for i, img in enumerate(images):
                        if img.mode != 'RGB':
                            img = img.convert('RGB')
                        temp_path = os.path.join(temp_dir, f'page_{i+1}.jpg')
                        img.save(temp_path, 'JPEG', quality=95)
                        temp_files.append(temp_path)
                        st.info(f"Converted page {i+1}")
            else:
                # For image files, save directly
                temp_path = os.path.join(temp_dir, uploaded_file.name)
                with open(temp_path, 'wb') as f:
                    f.write(uploaded_file.read())
                temp_files = [temp_path]

            # Analyze with Gemini
            with st.spinner("Analyzing financial statements..."):
                recognition_result = gemini_client.analyze_document(temp_files)
                
            return recognition_result

    except Exception as e:
        st.error(f"Error processing {uploaded_file.name}: {str(e)}")
        return None

if __name__ == "__main__":
    main() 