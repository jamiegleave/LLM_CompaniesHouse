import streamlit as st
import pandas as pd
import plotly.figure_factory as ff
import plotly.graph_objects as go
from src.gemini_client import GeminiClient
from src.download_accounts import CompaniesHouseDownloader
from src.cache_manager import RedisCache
import asyncio
import logging
from pathlib import Path
import json
import os
from datetime import datetime
from io import BytesIO

logger = logging.getLogger(__name__)

# Initialize Redis cache
redis_cache = RedisCache()

def calculate_roce(statements, year):
    """Calculate ROCE for a given year's statements"""
    try:
        pl_data = statements.get("profit_and_loss", {}).get(year, {})
        bs_data = statements.get("balance_sheet", {}).get(year, {})
        
        # Try to get Operating Profit, fallback to Profit Before Taxation
        operating_profit = pl_data.get("Operating Profit")
        if operating_profit is None:
            operating_profit = pl_data.get("Profit Before Taxation", 0)
        
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

def calculate_metrics(statements, year):
    """Calculate key financial metrics for a given year"""
    try:
        pl_data = statements.get("profit_and_loss", {}).get(year, {})
        bs_data = statements.get("balance_sheet", {}).get(year, {})
        
        # Calculate capital employed (ROCE denominator)
        capital_employed = bs_data.get("Total Assets Less Current Liabilities")
        if not capital_employed:
            total_assets = bs_data.get("Total Fixed Assets", 0) + bs_data.get("Total Current Assets", 0)
            current_liabilities = bs_data.get("Creditors: Amounts Falling Due Within One Year", 0)
            capital_employed = total_assets + current_liabilities
        
        metrics = {
            "ROCE (%)": calculate_roce(statements, year),
            "Capital Employed": capital_employed,  # Added ROCE denominator
            "Turnover": pl_data.get("Turnover"),
            "Gross Margin (%)": (pl_data.get("Gross Profit", 0) / pl_data.get("Turnover", 1)) * 100 if pl_data.get("Turnover") else None,
            "Operating Margin (%)": (pl_data.get("Operating Profit", 0) / pl_data.get("Turnover", 1)) * 100 if pl_data.get("Turnover") else None,
            "Net Profit Margin (%)": (pl_data.get("Profit for the Financial Year", 0) / pl_data.get("Turnover", 1)) * 100 if pl_data.get("Turnover") else None,
            "Asset Turnover": pl_data.get("Turnover", 0) / bs_data.get("Total Assets Less Current Liabilities", 1) if bs_data.get("Total Assets Less Current Liabilities") else None
        }
        return {k: round(v, 1) if v is not None else None for k, v in metrics.items()}
    except Exception as e:
        logger.error(f"Error calculating metrics: {str(e)}")
        return None

def load_company_data(company_number: str, api_key: str):
    """Load company data from cache or fetch new"""
    try:
        # Check cache first
        cached_data = redis_cache.get_company_data(company_number)
        if cached_data:
            logger.info(f"Cache hit for company {company_number}")
            return cached_data["company_details"], cached_data["statements"]
            
        # Fetch new data if not cached
        logger.info(f"Cache miss for company {company_number}, fetching from Companies House")
        downloader = CompaniesHouseDownloader(company_number)
        company_details = asyncio.run(downloader.get_company_details())
        downloaded_files = asyncio.run(downloader.download_all_accounts())
        
        if not downloaded_files:
            return None, None
            
        # Process files with Gemini
        gemini_client = GeminiClient(api_key)
        for filename, content in downloaded_files:
            file_obj = BytesIO(content)
            file_obj.name = filename
            result = gemini_client.analyze_document(file_obj, "application/pdf")
            
        consolidated_result = gemini_client.consolidate_statements()
        if consolidated_result.success:
            # Cache the results using Redis
            redis_cache.set_company_data(
                company_number=company_number,
                company_details=company_details,
                statements=consolidated_result.extracted_data
            )
            return company_details, consolidated_result.extracted_data
            
    except Exception as e:
        logger.error(f"Error loading company {company_number}: {str(e)}")
        return None, None

def create_metric_visualization(df, metric_name):
    """Create line chart for selected metric"""
    fig = go.Figure()
    
    # Determine if metric is a percentage
    is_percentage = "%" in metric_name
    
    for company in df.index:
        fig.add_trace(go.Scatter(
            x=df.columns,
            y=df.loc[company],
            name=company,
            mode='lines+markers',
            hovertemplate=(
                f"{company}<br>"
                f"Year: %{{x}}<br>"
                f"{metric_name}: %{{y:.1f}}{'%' if is_percentage else ''}<br>"
            )
        ))
    
    fig.update_layout(
        title=f"{metric_name} by Company",
        xaxis_title="Year",
        yaxis_title=metric_name,
        hovermode='x unified',
        height=400
    )
    return fig

def create_heatmap(df, metric_name):
    """Create heatmap with 5-year period chunks on x-axis"""
    # Determine if metric is a percentage
    is_percentage = "%" in metric_name
    
    # Group years into 5-year periods
    all_years = sorted(df.columns)
    period_data = {}
    for i in range(0, len(all_years), 5):
        years = all_years[i:i + 5]
        if len(years) == 5:  # Only use complete 5-year periods
            period_name = f"{years[0]}-{years[-1]}"
            period_data[period_name] = df[years].mean(axis=1)
    
    # Create new DataFrame with periods
    period_df = pd.DataFrame(period_data)
    
    # Create heatmap with simpler color scale and better text visibility
    fig = ff.create_annotated_heatmap(
        z=period_df.values,
        x=period_df.columns.tolist(),
        y=period_df.index.tolist(),
        annotation_text=[[f"{v:.1f}{'%' if is_percentage else ''}" if pd.notnull(v) else "" for v in row] for row in period_df.values],
        colorscale=[
            [0, 'rgb(255,255,255)'],      # White
            [1, 'rgb(200,220,255)']       # Very light blue
        ],
        showscale=False,
        hoverongaps=False,
        font_colors=['black'],  # Force black text for all cells
    )
    
    # Improve layout
    fig.update_layout(
        title=f"{metric_name} by Company (5-Year Periods)",
        xaxis_title="Period",
        yaxis_title="Company",
        height=max(300, len(df.index) * 80),  # Increased height
        margin=dict(t=50, l=200),
        xaxis=dict(
            side='bottom',
            tickangle=45
        ),
        yaxis=dict(
            side='left',
            tickmode='array',
            ticktext=df.index,
            tickfont=dict(size=12)
        )
    )
    
    # Update cell properties
    fig.update_traces(
        xgap=5,  # Increased gap between cells
        ygap=5,
        hovertemplate=(
            "<b>%{y}</b><br>" +
            "Period: %{x}<br>" +
            f"{metric_name}: %{{z:.1f}}{'%' if is_percentage else ''}<br>" +
            "<extra></extra>"
        )
    )
    
    # Update annotations (text) properties
    for annotation in fig.layout.annotations:
        annotation.update(
            font=dict(
                size=14,          # Larger font
                color='black',    # Force black text
                family='Arial'    # Clear font family
            )
        )
    
    return fig

def get_cached_companies():
    """Get list of all cached companies with their details"""
    try:
        companies = []
        # Get all keys from Redis that start with 'company:'
        for key in redis_cache.redis_client.keys('company:*'):
            company_data = redis_cache.get_company_data(key.replace('company:', ''))
            if company_data and 'company_details' in company_data:
                details = company_data['company_details']
                # Only add if we have both name and number
                if details.get('name') and details.get('number'):
                    companies.append({
                        'name': details['name'],
                        'number': details['number']
                    })
        return sorted(companies, key=lambda x: x['name'])
    except Exception as e:
        logger.error(f"Error fetching cached companies: {str(e)}")
        return []

def sectoral_analysis():
    st.title("Sectoral Financial Analysis")
    
    # Get and display cached companies
    cached_companies = get_cached_companies()
    if not cached_companies:
        st.warning("No companies available in cache. Please analyze some companies first.")
        return
        
    selected_companies = st.multiselect(
        "Select Companies to Compare",
        options=cached_companies,
        format_func=lambda x: x['name'],  # Show only company name in dropdown
        key='company_selector'
    )
    
    # Extract company numbers from selections
    company_numbers = [company['number'] for company in selected_companies]
    
    # API key input
    api_key = st.sidebar.text_input("Google API Key", 
                                    type="password", 
                                    help="Enter your Google API key",
                                    value=os.getenv('GEMINI_API_KEY','')
                                    )
    
    if not api_key:
        st.warning("Please enter your Google API key")
        return
        
    # Year range selection
    current_year = datetime.now().year
    year_range = st.slider(
        "Select Year Range",
        min_value=current_year-50,
        max_value=current_year,
        value=(current_year-5, current_year),
        step=1
    )
    
    # Metric selection
    available_metrics = [
        "ROCE (%)",
        "Capital Employed",
        "Turnover",
        "Gross Margin (%)",
        "Operating Margin (%)",
        "Net Profit Margin (%)",
        "Asset Turnover"
    ]
    
    selected_metric = st.selectbox(
        "Select Financial Metric",
        available_metrics,
        index=0
    )
    
    if st.button("Analyze Companies") and company_numbers:
        with st.spinner("Analyzing companies..."):
            # Initialize data structure for metrics
            metric_data = {}
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
                metric_data[company_number] = {}
                
                # Calculate metrics for each year in range
                for year in range(year_range[0], year_range[1] + 1):
                    metrics = calculate_metrics(statements.get("statements", {}), str(year))
                    if metrics and metrics.get(selected_metric) is not None:
                        metric_data[company_number][str(year)] = metrics[selected_metric]
            
            if metric_data:
                # Create DataFrame
                df = pd.DataFrame(metric_data).T
                df.index = [company_names.get(num, num) for num in df.index]
                
                # Show visualizations
                tab1, tab2 = st.tabs(["Line Chart", "Heatmap"])
                
                with tab1:
                    st.plotly_chart(
                        create_metric_visualization(df, selected_metric),
                        use_container_width=True
                    )
                
                with tab2:
                    st.plotly_chart(
                        create_heatmap(df, selected_metric),
                        use_container_width=True
                    )
                
                # Display summary statistics
                st.subheader("Summary Statistics")
                summary_df = df.describe()
                st.dataframe(summary_df.style.format("{:.1f}"))
                
                # Download options
                csv = df.to_csv()
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name="financial_analysis.csv",
                    mime="text/csv"
                )
            else:
                st.error("No data available for analysis")

if __name__ == "__main__":
    sectoral_analysis() 