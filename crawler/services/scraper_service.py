import logging
from ..validators import CryptoAddressValidator
import cloudscraper
from bs4 import BeautifulSoup
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class MistTrackScraperService:
    def __init__(self):
        self.base_url = "https://misttrack.io/aml_risks"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "application/json"
        }
        self.session = self._create_scraper_session()
        self.validator = CryptoAddressValidator()

    @staticmethod
    def _create_scraper_session():
        return cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'mobile': False
            }
        )

    async def _make_request(self, url: str, method: str = "GET", data: Optional[Dict] = None, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make HTTP request with error handling and retries"""
        try:
            logger.debug(f"Making {method} request to {url}")
            
            if method == "GET":
                response = self.session.get(url, headers=self.headers, params=params)
            else:
                response = self.session.post(url, headers=self.headers, json=data)
            
            response.raise_for_status()
            return {"success": True, "data": response}
            
        except Exception as e:
            logger.error(f"Request failed: {str(e)}")
            return {"success": False, "error": str(e)}

    async def get_address_info(self, address: str) -> Dict[str, Any]:
        """Get information about a crypto address"""
        if not self.validator.validate(address):
            return {"success": False, "error": "Invalid address format"}

        url = f"{self.base_url}/address/{address}"
        response = await self._make_request(url)
        
        if not response["success"]:
            return response

        try:
            soup = BeautifulSoup(response["data"].text, 'html.parser')
            return {
                "success": True,
                "data": {
                    "risk_score": self._extract_risk_score(soup),
                    "labels": self._extract_labels(soup),
                    "transactions": self._extract_transactions(soup),
                    "related_addresses": self._extract_related_addresses(soup)
                }
            }
        except Exception as e:
            logger.error(f"Error parsing address info: {str(e)}")
            return {"success": False, "error": "Error parsing response"}

    def _extract_risk_score(self, soup: BeautifulSoup) -> Optional[int]:
        try:
            risk_element = soup.find('div', {'class': 'risk-score'})
            return int(risk_element.text) if risk_element else None
        except Exception as e:
            logger.warning(f"Error extracting risk score: {str(e)}")
            return None

    def _extract_labels(self, soup: BeautifulSoup) -> list:
        try:
            labels_div = soup.find('div', {'class': 'labels'})
            return [label.text for label in labels_div.find_all('span')] if labels_div else []
        except Exception as e:
            logger.warning(f"Error extracting labels: {str(e)}")
            return []

    def _extract_transactions(self, soup: BeautifulSoup) -> list:
        try:
            transactions_table = soup.find('table', {'class': 'transactions'})
            if not transactions_table:
                return []
                
            transactions = []
            for row in transactions_table.find_all('tr')[1:]:  # Skip header row
                cols = row.find_all('td')
                if len(cols) >= 4:
                    transactions.append({
                        'hash': cols[0].text.strip(),
                        'from': cols[1].text.strip(),
                        'to': cols[2].text.strip(),
                        'amount': cols[3].text.strip()
                    })
            return transactions
        except Exception as e:
            logger.warning(f"Error extracting transactions: {str(e)}")
            return []

    def _extract_related_addresses(self, soup: BeautifulSoup) -> list:
        try:
            related_div = soup.find('div', {'class': 'related-addresses'})
            return [addr.text for addr in related_div.find_all('a')] if related_div else []
        except Exception as e:
            logger.warning(f"Error extracting related addresses: {str(e)}")
            return []
