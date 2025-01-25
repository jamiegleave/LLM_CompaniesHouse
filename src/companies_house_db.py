import psycopg2
from psycopg2.extras import RealDictCursor
import logging
from typing import Optional, Dict, List
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class CompaniesHouseDB:
    def __init__(self):
        """Initialize database connection using environment variables"""
        try:
            self.conn = psycopg2.connect(
                dbname=os.getenv('DB_NAME'),
                user=os.getenv('DB_USER'),
                password=os.getenv('DB_PASSWORD'),
                host=os.getenv('DB_HOST'),
                port=os.getenv('DB_PORT', '5432')
            )
            logger.info("Successfully connected to Companies House database")
        except Exception as e:
            logger.error(f"Error connecting to database: {str(e)}")
            raise

    def get_company_by_number(self, company_number: str) -> Optional[Dict]:
        """
        Fetch company details by company number
        
        Args:
            company_number: The company registration number
            
        Returns:
            Dictionary containing company details or None if not found
        """
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM companies 
                    WHERE company_number = %s
                """, (company_number,))
                
                result = cur.fetchone()
                if result:
                    # Convert datetime objects to strings for JSON serialization
                    for key, value in result.items():
                        if isinstance(value, datetime):
                            result[key] = value.isoformat()
                    return dict(result)
                return None
                
        except Exception as e:
            logger.error(f"Error fetching company {company_number}: {str(e)}")
            return None

    def search_companies(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Search companies by name or number
        
        Args:
            query: Search term for company name or number
            limit: Maximum number of results to return
            
        Returns:
            List of matching companies
        """
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM companies 
                    WHERE company_name ILIKE %s 
                    OR company_number ILIKE %s
                    LIMIT %s
                """, (f"%{query}%", f"%{query}%", limit))
                
                results = cur.fetchall()
                # Convert datetime objects to strings
                for result in results:
                    for key, value in result.items():
                        if isinstance(value, datetime):
                            result[key] = value.isoformat()
                return results
                
        except Exception as e:
            logger.error(f"Error searching companies with query {query}: {str(e)}")
            return []

    def get_company_status_stats(self) -> Dict[str, int]:
        """
        Get statistics on company statuses
        
        Returns:
            Dictionary with status counts
        """
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT company_status, COUNT(*) as count 
                    FROM companies 
                    GROUP BY company_status
                """)
                
                results = cur.fetchall()
                return {row['company_status']: row['count'] for row in results}
                
        except Exception as e:
            logger.error(f"Error getting company status stats: {str(e)}")
            return {}

    def get_companies_by_sic_code(self, sic_code: str) -> List[Dict]:
        """
        Get companies by SIC code
        
        Args:
            sic_code: The SIC code to search for
            
        Returns:
            List of companies with matching SIC code
        """
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT * FROM companies 
                    WHERE sic_code_text_1 LIKE %s 
                    OR sic_code_text_2 LIKE %s
                    OR sic_code_text_3 LIKE %s
                    OR sic_code_text_4 LIKE %s
                """, (f"%{sic_code}%",) * 4)
                
                results = cur.fetchall()
                # Convert datetime objects to strings
                for result in results:
                    for key, value in result.items():
                        if isinstance(value, datetime):
                            result[key] = value.isoformat()
                return results
                
        except Exception as e:
            logger.error(f"Error fetching companies by SIC code {sic_code}: {str(e)}")
            return []

    def get_company_details(self, company_number: str) -> Dict:
        """
        Get formatted company details for display
        
        Args:
            company_number: The company registration number
            
        Returns:
            Dictionary containing formatted company details for display
        """
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("""
                    SELECT 
                        company_name,
                        company_number,
                        company_status,
                        company_category,
                        incorporation_date,
                        reg_address_line1,
                        reg_address_line2,
                        reg_address_post_town,
                        reg_address_county,
                        reg_address_country,
                        reg_address_post_code,
                        sic_code_text_1,
                        sic_code_text_2,
                        sic_code_text_3,
                        sic_code_text_4,
                        accounts_category,
                        accounts_next_due_date,
                        accounts_last_made_up_date
                    FROM companies 
                    WHERE company_number = %s
                """, (company_number,))
                
                result = cur.fetchone()
                if not result:
                    return None
                
                # Convert datetime objects to formatted strings
                for key, value in result.items():
                    if isinstance(value, datetime):
                        result[key] = value.strftime('%d %B %Y')
                
                # Format address
                address_parts = [
                    result.get('reg_address_line1'),
                    result.get('reg_address_line2'),
                    result.get('reg_address_post_town'),
                    result.get('reg_address_county'),
                    result.get('reg_address_post_code')
                ]
                formatted_address = ', '.join(filter(None, address_parts))
                
                # Format SIC codes
                sic_codes = [
                    result.get('sic_code_text_1'),
                    result.get('sic_code_text_2'),
                    result.get('sic_code_text_3'),
                    result.get('sic_code_text_4')
                ]
                formatted_sic_codes = list(filter(None, sic_codes))
                
                return {
                    "name": result.get('company_name'),
                    "number": result.get('company_number'),
                    "status": result.get('company_status'),
                    "type": result.get('company_category'),
                    "incorporated": result.get('incorporation_date'),
                    "address": formatted_address,
                    "sic_codes": formatted_sic_codes,
                    "accounts": {
                        "category": result.get('accounts_category'),
                        "next_due": result.get('accounts_next_due_date'),
                        "last_made_up": result.get('accounts_last_made_up_date')
                    }
                }
                
        except Exception as e:
            logger.error(f"Error fetching company details for {company_number}: {str(e)}")
            return None

    def __del__(self):
        """Close database connection when object is destroyed"""
        try:
            if hasattr(self, 'conn'):
                self.conn.close()
                logger.info("Database connection closed")
        except Exception as e:
            logger.error(f"Error closing database connection: {str(e)}") 