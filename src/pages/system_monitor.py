import streamlit as st
import pandas as pd
from src.cache_manager import RedisCache
from src.download_accounts import CompaniesHouseDownloader
import asyncio
import logging
from src.gemini_client import GeminiClient
import os
from io import BytesIO

logger = logging.getLogger(__name__)

def run_async(coroutine):
    """Helper function to run async code in synchronous context"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coroutine)

def system_monitor():
    st.title("System Monitor")
    
    # Initialize Redis cache
    redis_cache = RedisCache()
    
    # Create tabs for different monitoring aspects
    tab_health, tab_cache, tab_downloads = st.tabs(["System Health", "Cache Management", "Download Monitor"])
    
    with tab_health:
        st.header("System Health")
        
        # Check Redis connection
        redis_status = redis_cache.is_healthy()
        status_color = "green" if redis_status else "red"
        st.markdown(f"""
        ### Redis Connection
        <span style='color:{status_color}'>●</span> {'Connected' if redis_status else 'Disconnected'}
        """, unsafe_allow_html=True)
        
        # Add refresh button
        if st.button("Refresh Status"):
            st.rerun()
    
    with tab_cache:
        st.header("Cache Management")
        
        # Cache operations section
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Delete Cache Entry")
            company_number = st.text_input(
                "Company Number",
                help="Enter the company number to delete its cache entry"
            )
            
            if st.button("Delete Entry"):
                if company_number:
                    if redis_cache.delete_company_data(company_number):
                        st.success(f"Successfully deleted cache for company {company_number}")
                    else:
                        st.error(f"No cache entry found for company {company_number}")
                else:
                    st.warning("Please enter a company number")
        
        with col2:
            st.subheader("Cache Statistics")
            # Add cache statistics if available through Redis
            # This is a placeholder - implement based on your needs
            st.info("Cache statistics coming soon...")
    
    with tab_downloads:
        st.header("Download Monitor")
        
        # Get API key from sidebar
        api_key = st.sidebar.text_input(
            "Google API Key",
            type="password",
            help="Enter your Google API key",
            value=os.getenv('GEMINI_API_KEY','')
        )

        if not api_key:
            st.warning("Please enter your Google API key to process documents.")
            return
            
        # Company download section
        st.subheader("Download and Process Company Accounts")
        company_number = st.text_input(
            "Company Number to Download",
            help="Enter the company number to download its accounts"
        )
        
        if st.button("Start Download and Processing"):
            if company_number:
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                try:
                    # Check cache first
                    cache_result = redis_cache.get_company_data(company_number)
                    cached_results = None
                    cached_company_details = None
                    
                    if cache_result:  # Only unpack if we got a result
                        cached_results = cache_result.get("statements")
                        cached_company_details = cache_result.get("company_details")
                    
                    if cached_results:
                        status_text.text("Found cached results!")
                        progress_bar.progress(100)
                        
                        # Display cached results
                        st.success("Retrieved from cache")
                        st.write("Company Details:", cached_company_details)
                        st.json(cached_results)
                        
                    else:
                        # Initialize downloader and Gemini client
                        downloader = CompaniesHouseDownloader(company_number)
                        gemini_client = GeminiClient(api_key=api_key)
                        
                        # Phase 1: Get company details (10%)
                        status_text.text("Fetching company details...")
                        progress_bar.progress(10)
                        
                        company_details = run_async(downloader.get_company_details())
                        if company_details:
                            st.write("Company Name:", company_details['name'])
                            progress_bar.progress(20)
                        
                        # Phase 2: Download accounts (20-40%)
                        status_text.text("Downloading account files...")
                        downloaded_files = run_async(downloader.download_all_accounts())
                        
                        if not downloaded_files:
                            status_text.text("No files found to download")
                            progress_bar.progress(100)
                            return
                            
                        progress_bar.progress(40)
                        
                        # Display download results
                        st.write("Downloaded Files:")
                        for filename, content in downloaded_files:
                            st.write(f"✓ {filename}")
                        
                        # Phase 3: Process with Gemini (40-80%)
                        status_text.text("Processing files with Gemini...")
                        
                        for idx, (filename, content) in enumerate(downloaded_files):
                            current_progress = 40 + (40 * (idx + 1) / len(downloaded_files))
                            progress_bar.progress(int(current_progress))
                            status_text.text(f"Processing {filename}...")
                            
                            # Create file-like object
                            file_obj = BytesIO(content)
                            file_obj.name = filename
                            
                            # Process with Gemini - use run_async to handle the async call
                            result = run_async(gemini_client.analyze_document(
                                file_obj,
                                mime_type='application/pdf'
                            ))
                            
                            if not result or not result.success:
                                st.error(f"Failed to process {filename}")
                                continue
                        
                        # Phase 4: Consolidate results (80-90%)
                        status_text.text("Consolidating results...")
                        progress_bar.progress(80)
                        
                        consolidated_result = gemini_client.consolidate_statements()
                        
                        if not consolidated_result.success:
                            st.error("Failed to consolidate results")
                            return
                            
                        # Phase 5: Cache results (90-100%)
                        status_text.text("Caching results...")
                        progress_bar.progress(90)
                        
                        cache_success = redis_cache.set_company_data(
                            company_number=company_number,
                            company_details=company_details,
                            statements=consolidated_result.extracted_data
                        )
                        
                        if cache_success:
                            status_text.text("Processing complete!")
                            progress_bar.progress(100)
                            
                            # Display results
                            st.success("Successfully processed and cached")
                            st.write("Company Details:", company_details)
                            st.json(consolidated_result.extracted_data)
                        else:
                            st.warning("Processing complete but caching failed")
                            st.json(consolidated_result.extracted_data)
                        
                except Exception as e:
                    st.error(f"Error during processing: {str(e)}")
                    logger.error(f"Processing error: {str(e)}")
                    progress_bar.progress(100)
        
        # Recent Activity Log
        st.subheader("Recent Activity")
        
        # Create a placeholder for the activity log
        # This could be enhanced to show real activity from a database or log file
        activity_data = {
            'Timestamp': [],
            'Action': [],
            'Status': [],
            'Details': []
        }
        
        # Display activity log as a table
        if activity_data['Timestamp']:
            df = pd.DataFrame(activity_data)
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No recent activity to display")

if __name__ == "__main__":
    system_monitor() 