import streamlit as st
import pandas as pd
import plotly.figure_factory as ff
import plotly.graph_objects as go
from src.gemini_client import GeminiClient
from src.download_accounts import CompaniesHouseDownloader
import asyncio
import logging
from pathlib import Path
import json
import os
from datetime import datetime
from io import BytesIO

logger = logging.getLogger(__name__)

def calculate_roce(statements, year):
    """Calculate ROCE for a given year's statements"""
    try:
        pl_data = statements.get("profit_and_loss", {}).get(year, {})
        bs_data = statements.get("balance_sheet", {}).get(year, {})
        
        operating_profit = pl_data.get("Operating Profit", 0)
        capital_employed = bs_data.get("Total Assets Less Current Liabilities")
        
        # Alternative calculation if total assets less current liabilities isn't available
        if not capital_employed:
            total_assets = bs_data.get("Total Fixed Assets", 0) + bs_data.get("Total Current Assets", 0)
            current_liabilities = bs_data.get("Creditors: Amounts Falling Due Within One Year", 0)
            capital_employed = total_assets + current_liabilities
        
        if capital_employed and capital_employed != 0:
            return (operating_profit / capital_employed) * 100
        return None
    except Exception as e:
        logger.error(f"Error calculating ROCE: {str(e)}")
        return None

def load_company_data(company_number: str, api_key: str):
    """Load company data from cache or fetch new"""
    cache_dir = Path("cache")
    cache_file = cache_dir / f"{company_number}.json"
    
    if cache_file.exists():
        with open(cache_file, "r") as f:
            cached_data = json.load(f)
            if datetime.now().timestamp() - cached_data["timestamp"] < 86400:  # 24 hours
                return cached_data["company_details"], cached_data["statements"]
    
    # Fetch new data if not cached or expired
    try:
        downloader = CompaniesHouseDownloader(company_number)
        company_details = asyncio.run(downloader.get_company_details())
        downloaded_files = asyncio.run(downloader.download_all_accounts())
        
        if not downloaded_files:
            return None, None
            
        # Process files with Gemini
        gemini_client = GeminiClient(api_key)
        for filename, content in downloaded_files:
            # Create a file-like object from the bytes content
            file_obj = BytesIO(content)
            file_obj.name = filename  # Add name attribute required by Gemini
            result = gemini_client.analyze_document(file_obj, "application/pdf")
            
        consolidated_result = gemini_client.consolidate_statements()
        if consolidated_result.success:
            # Cache the results
            cache_dir.mkdir(exist_ok=True)
            with open(cache_file, "w") as f:
                json.dump({
                    "timestamp": datetime.now().timestamp(),
                    "company_details": company_details,
                    "statements": consolidated_result.extracted_data
                }, f)
            return company_details, consolidated_result.extracted_data
            
    except Exception as e:
        logger.error(f"Error loading company {company_number}: {str(e)}")
        return None, None

def sectoral_analysis():
    st.title("Sectoral ROCE Analysis")
    
    # API key input
    api_key = st.sidebar.text_input("Google API Key", 
                                    type="password", 
                                    help="Enter your Google API key",
                                    value=os.getenv('GEMINI_API_KEY','')
                                    )
    
    if not api_key:
        st.warning("Please enter your Google API key")
        return
        
    # Company numbers input
    company_numbers = st.text_area(
        "Enter Companies House Numbers (one per line)",
        help="Enter multiple 8-digit company registration numbers, one per line"
    ).strip().split('\n')
    
    # Year range selection
    current_year = datetime.now().year
    year_range = st.slider(
        "Select Year Range",
        min_value=current_year-30,
        max_value=current_year,
        value=(current_year-5, current_year),
        step=1
    )
    
    if st.button("Analyze Companies") and company_numbers:
        with st.spinner("Analyzing companies..."):
            # Initialize data structure for ROCE values
            roce_data = {}
            company_names = {}
            
            # Process each company
            for company_number in company_numbers:
                company_number = company_number.strip()
                if not company_number:
                    continue
                    
                company_details, statements = load_company_data(company_number, api_key)
                if not statements:
                    st.warning(f"Could not load data for company {company_number}")
                    continue
                
                company_names[company_number] = company_details.get("name", company_number)
                roce_data[company_number] = {}
                
                # Calculate ROCE for each year in range
                for year in range(year_range[0], year_range[1] + 1):
                    roce = calculate_roce(statements.get("statements", {}), str(year))
                    if roce is not None:
                        roce_data[company_number][str(year)] = roce
            
            if roce_data:
                # Create DataFrame for heatmap
                df = pd.DataFrame(roce_data).T
                
                # Replace company numbers with names in index
                df.index = [company_names.get(num, num) for num in df.index]
                
                # Create heatmap
                fig = ff.create_annotated_heatmap(
                    z=df.values,
                    x=df.columns.tolist(),
                    y=df.index.tolist(),
                    annotation_text=[[f"{v:.1f}%" if pd.notnull(v) else "" for v in row] for row in df.values],
                    colorscale="RdYlBu",
                    showscale=True
                )
                
                fig.update_layout(
                    title="Return on Capital Employed (ROCE) by Company",
                    xaxis_title="Year",
                    yaxis_title="Company",
                    height=400 + (len(company_numbers) * 30)
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Display summary statistics
                st.subheader("Summary Statistics")
                summary_df = df.describe()
                st.dataframe(summary_df.style.format("{:.1f}%"))
                
                # Download options
                csv = df.to_csv()
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name="roce_analysis.csv",
                    mime="text/csv"
                )
            else:
                st.error("No data available for analysis")

if __name__ == "__main__":
    sectoral_analysis() 