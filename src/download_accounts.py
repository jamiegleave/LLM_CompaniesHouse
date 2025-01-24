import aiohttp
import asyncio
from bs4 import BeautifulSoup
from datetime import datetime
import re
import logging
import random

# Get logger
logger = logging.getLogger(__name__)

class CompaniesHouseDownloader:
    def __init__(self, company_number):
        self.company_number = company_number
        self.base_url = "https://find-and-update.company-information.service.gov.uk"
        # Set headers to mimic a browser
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.semaphore = asyncio.Semaphore(3)  # Limit concurrent downloads
        
    async def get_filing_history_page(self, page=1):
        """Fetch a single page of filing history with exponential backoff"""
        url = f"{self.base_url}/company/{self.company_number}/filing-history"
        params = {'page': page} if page > 1 else {}
        
        max_retries = 5
        base_delay = 2
        max_delay = 30
        
        for attempt in range(max_retries):
            try:
                async with aiohttp.ClientSession(headers=self.headers) as session:
                    async with session.get(url, params=params) as response:
                        if response.status >= 500:
                            raise aiohttp.ClientError(f"Server error: {response.status}")
                        response.raise_for_status()
                        return await response.text()
                            
            except aiohttp.ClientError as e:
                if attempt == max_retries - 1:
                    logger.error(f"Failed to fetch page {page} after {max_retries} attempts: {str(e)}")
                    raise
                    
                delay = min(base_delay * (2 ** attempt) + random.uniform(0, 1), max_delay)
                logger.warning(f"Request failed, retrying in {delay:.1f} seconds (attempt {attempt + 1}/{max_retries})")
                await asyncio.sleep(delay)
                
        raise Exception(f"Failed to fetch page {page} after {max_retries} attempts")
    
    def extract_pdf_links(self, html):
        """Extract PDF links from the page HTML (unchanged as it's sync parsing)"""
        soup = BeautifulSoup(html, 'html.parser')
        pdf_links = []
        
        rows = soup.find_all('tr')
        for row in rows:
            description_cell = row.find('td', recursive=True, 
                                    string=lambda text: isinstance(text, str) and 
                                    any(term in text for term in ["accounts", "Accounts"]))
            
            if not description_cell:
                strong_tag = row.find('strong', string=lambda text: isinstance(text, str) and 
                                    any(term in text for term in ["accounts", "Accounts"]))
                if strong_tag:
                    description_cell = strong_tag.find_parent('td')
            
            if description_cell:
                pdf_link = row.find('a', href=lambda href: href and '/document?format=pdf' in href)
                if pdf_link:
                    full_text = description_cell.get_text()
                    date_match = re.search(r'made up to (\d{1,2} [A-Za-z]+ \d{4})', full_text)
                    if date_match:
                        date_str = date_match.group(1)
                        try:
                            date_obj = datetime.strptime(date_str, '%d %B %Y')
                            year = date_obj.year
                        except ValueError:
                            year = 'unknown'
                    else:
                        year = 'unknown'
                    
                    full_url = pdf_link['href']
                    pdf_links.append((f"{self.base_url}{full_url}", year))
        
        return pdf_links
    
    def has_next_page(self, html):
        """Check if there's a next page (unchanged as it's sync parsing)"""
        soup = BeautifulSoup(html, 'html.parser')
        next_link = soup.find('a', {'rel': 'next'})
        return bool(next_link)
    
    async def download_pdf(self, url, year):
        """Download a single PDF with rate limiting"""
        async with self.semaphore:  # Limit concurrent downloads
            try:
                async with aiohttp.ClientSession(headers=self.headers) as session:
                    async with session.get(url) as response:
                        response.raise_for_status()
                        content = await response.read()
                        
                        # Verify PDF content
                        if content.startswith(b'%PDF'):
                            filename = f"company_{self.company_number}_accounts_{year}.pdf"
                            logger.info(f"Successfully downloaded {filename}")
                            return filename, content
                        else:
                            logger.warning(f"Downloaded content is not a valid PDF for year {year}")
                            return None
                            
            except Exception as e:
                logger.error(f"Error downloading PDF for year {year}: {str(e)}")
                return None
            
            # Rate limiting delay
            await asyncio.sleep(2)
    
    async def download_all_accounts(self):
        """Main method to download all account PDFs"""
        logger.info(f"Starting download process for company {self.company_number}")
        page = 1
        pdf_links = []
        
        # First phase: Get all PDF links from all pages
        while True:
            logger.info(f"Processing page {page}...")
            html = await self.get_filing_history_page(page)
            page_links = self.extract_pdf_links(html)
            pdf_links.extend(page_links)
            
            if not self.has_next_page(html):
                logger.info(f"No more pages to process. Found {len(pdf_links)} PDF links.")
                break
                
            page += 1
            await asyncio.sleep(2)  # Be nice between pages
        
        if not pdf_links:
            logger.warning("No PDF links found")
            return []
            
        # Second phase: Download all PDFs concurrently
        logger.info(f"Starting download of {len(pdf_links)} PDFs...")
        downloaded_files = []
        failed_downloads = []
        
        async with asyncio.TaskGroup() as tg:
            # Create tasks for all downloads
            tasks = [tg.create_task(self.download_pdf(url, year)) for url, year in pdf_links]
        
        # Process results, handling None values
        for task, (url, year) in zip(tasks, pdf_links):
            result = task.result()
            if result:
                downloaded_files.append(result)
            else:
                failed_downloads.append((url, year))
        
        # Log download statistics
        logger.info(f"Download process complete. Successfully downloaded {len(downloaded_files)} files.")
        if failed_downloads:
            logger.warning(f"Failed to download {len(failed_downloads)} files.")
            for url, year in failed_downloads:
                logger.warning(f"Failed download: {url} (year: {year})")
        
        # Return successful downloads even if some failed
        return downloaded_files if downloaded_files else None
    
    async def get_company_details(self):
        """Extract company name and number from the filing history page"""
        html = await self.get_filing_history_page()
        soup = BeautifulSoup(html, 'html.parser')
        
        company_name = soup.select_one(".company-header > h1").text.strip()
        company_number = soup.select_one("#company-number > strong").text.strip()
        
        return {
            'name': company_name,
            'number': company_number
        }