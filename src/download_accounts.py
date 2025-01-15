import requests
from bs4 import BeautifulSoup
import os
import time
from datetime import datetime
import re

class CompaniesHouseDownloader:
    def __init__(self, company_number):
        self.company_number = company_number
        self.base_url = "https://find-and-update.company-information.service.gov.uk"
        self.session = requests.Session()
        # Set headers to mimic a browser
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    def get_filing_history_page(self, page=1):
        url = f"{self.base_url}/company/{self.company_number}/filing-history"
        params = {'page': page} if page > 1 else {}
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.text
    
    def extract_pdf_links(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        pdf_links = []
                
        # Find all table rows
        rows = soup.find_all('tr')

        for row in rows:
            # Find description cell containing "Full accounts" in any nested element
            description_cell = row.find('td', recursive=True, 
                                    string=lambda text: isinstance(text, str) and "Full accounts" in text)
            
            if not description_cell:
                # Try finding it through the strong tag
                strong_tag = row.find('strong', string=lambda text: isinstance(text, str) and "Full accounts" in text)
                if strong_tag:
                    description_cell = strong_tag.find_parent('td')
            
            if description_cell:
                # Find PDF link in the same row
                pdf_link = row.find('a', href=lambda href: href and '/document?format=pdf' in href)
                if pdf_link:
                    # Extract date from description text (including nested elements)
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
                    
                    # Assuming base_url is defined somewhere
                    full_url = pdf_link['href']  # Remove self.base_url for testing
                    pdf_links.append((f"{self.base_url}/{full_url}", year))
        
        return pdf_links
    
    def has_next_page(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        next_link = soup.find('a', {'rel': 'next'})
        return bool(next_link)
    
    def download_pdf(self, url, year):
        response = self.session.get(url)
        response.raise_for_status()
        
        # Create downloads directory if it doesn't exist
        os.makedirs('downloads', exist_ok=True)
        
        # Create filename with company number and year
        filename = f"downloads/company_{self.company_number}_accounts_{year}.pdf"
        
        with open(filename, 'wb') as f:
            f.write(response.content)
        
        return filename
    
    def download_all_accounts(self):
        page = 1
        downloaded_files = []
        
        while True:
            print(f"Processing page {page}...")
            html = self.get_filing_history_page(page)
            pdf_links = self.extract_pdf_links(html)
            
            for url, year in pdf_links:
                try:
                    print(f"Downloading accounts for year {year}...")
                    filename = self.download_pdf(url, year)
                    downloaded_files.append(filename)
                    # Be nice to the server
                    time.sleep(2)
                except Exception as e:
                    print(f"Error downloading {url}: {str(e)}")
            
            if not self.has_next_page(html):
                break
                
            page += 1
            # Be nice to the server
            time.sleep(2)
        
        return downloaded_files

def main():
    # Example usage
    company_number = "00026538"  # Esso Petroleum Company Limited
    downloader = CompaniesHouseDownloader(company_number)
    
    try:
        downloaded_files = downloader.download_all_accounts()
        print("\nSuccessfully downloaded files:")
        for file in downloaded_files:
            print(f"- {file}")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()