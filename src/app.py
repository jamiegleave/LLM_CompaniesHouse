import streamlit as st
from .document_uploader import DocumentUploader
from .openrouter_client import OpenRouterClient
from .config import SUPPORTED_FORMATS, MAX_FILE_SIZE_MB
import pandas as pd
import json

def main():
    st.title("FinState Analyzer")
    
    # Add API key configuration in sidebar
    api_key = st.sidebar.text_input(
        "OpenRouter API Key",
        type="password",
        help="Enter your OpenRouter API key"
    )
    
    if not api_key:
        st.warning("Please enter your OpenRouter API key to enable document recognition.")
        return

    st.sidebar.header("Document Upload")

    # Initialize clients
    uploader = DocumentUploader(api_key=api_key)
    router_client = OpenRouterClient(api_key=api_key)

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
            
            with st.spinner("Converting document to images..."):
                # First, convert document to images
                upload_result = process_uploaded_file(uploaded_file, uploader)
                
                if not upload_result or not upload_result.success:
                    continue

            with st.spinner("Analyzing financial statements..."):
                # Then analyze with OpenRouter using all pages
                recognition_result = router_client.analyze_document(upload_result.image_bytes_list)
                
                if recognition_result.success:
                    display_results(recognition_result)
                else:
                    st.error(f"Analysis failed: {recognition_result.error}")

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

            # Create DataFrame for Profit & Loss
            pl_rows = []
            years = sorted([year for year in pl_data.keys() if year.isdigit()])
            
            # Get all unique line items
            line_items = set()
            for year in years:
                line_items.update(item["name"] for item in pl_data[year]["profit_and_loss"])
                if "other_comprehensive_income" in pl_data[year]:
                    line_items.update(item["name"] for item in pl_data[year]["other_comprehensive_income"])
            
            # Create rows for DataFrame
            for item_name in line_items:
                row = {"Line Item": item_name}
                for year in years:
                    # Check in profit_and_loss
                    value = next((item["value"] for item in pl_data[year]["profit_and_loss"] 
                                if item["name"] == item_name), None)
                    # If not found, check in other_comprehensive_income
                    if value is None and "other_comprehensive_income" in pl_data[year]:
                        value = next((item["value"] for item in pl_data[year]["other_comprehensive_income"] 
                                    if item["name"] == item_name), None)
                    row[year] = value
                pl_rows.append(row)
            
            # Add total comprehensive income
            pl_rows.append({
                "Line Item": "Total comprehensive income",
                **{year: pl_data[year].get("total_comprehensive_income") for year in years}
            })
            
            # Create and display DataFrame
            df = pd.DataFrame(pl_rows)
            
            # Format the DataFrame
            st.subheader("Profit & Loss Statement")
            
            # Style the DataFrame
            def style_negative_red(val):
                if isinstance(val, (int, float)) and val < 0:
                    return 'color: red'
                return ''
            
            styled_df = df.style\
                .format({col: '{:,.0f}' for col in years})\
                .applymap(style_negative_red, subset=years)\
                .set_properties(**{
                    'text-align': 'left',
                    'font-family': 'monospace',
                    'white-space': 'pre'
                })
            
            st.dataframe(styled_df, use_container_width=True)
            
    except Exception as e:
        st.error(f"Error displaying financial data: {str(e)}")

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

def process_uploaded_file(uploaded_file, uploader):
    """Process the uploaded file and return the result"""
    try:
        # First, convert document to images
        upload_result = uploader.recognize_document(uploaded_file)
        
        if not upload_result or not upload_result.success:
            st.error(f"Error processing {uploaded_file.name}: {upload_result.error if upload_result else 'Unknown error'}")
            return None
            
        return upload_result
        
    except Exception as e:
        st.error(f"Error processing {uploaded_file.name}: {str(e)}")
        return None

if __name__ == "__main__":
    main() 