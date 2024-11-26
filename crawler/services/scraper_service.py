import logging
import cloudscraper
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from typing import Dict, Any, Optional
from ..validators import CryptoAddressValidator
from ..scraper_undetected import UndetectedScraper
import json

logger = logging.getLogger(__name__)

class MistTrackScraperService:
    def __init__(self, address: str, network: str = 'ETH'):
        self.address = address
        self.network = network
        self.base_url = f"https://misttrack.io/aml_risks/{self.network}/{self.address}"
        self.validator = CryptoAddressValidator()
        self.scraper = UndetectedScraper()

    async def _make_request(self, url: str) -> Dict[str, Any]:
        """Make HTTP request using UndetectedScraper"""
        try:
            # 在事件循环的默认线程池中运行同步的scraper
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self.scraper.search_address,
                f"{self.network}/{self.address}"
            )
            
            if "error" in result:
                return {"success": False, "error": result["error"]}
            
            return {"success": True, "data": result}
            
        except Exception as e:
            logger.error(f"Error making request: {str(e)}")
            return {"success": False, "error": str(e)}

    async def get_address_info(self) -> Dict[str, Any]:
        """Get information about a crypto address"""
        logger.info(f"Getting info for address {self.address} on network {self.network}")
        
        valid, message, _ = self.validator.validate(self.address)
        if not valid:
            logger.error(f"Invalid address format: {self.address}")
            return {"success": False, "error": message}

        try:
            logger.info(f"Making request for address {self.address}")
            response = await self._make_request(self.base_url)
            
            if not response["success"]:
                logger.error(f"Request failed: {response['error']}")
                return response
            
            # 直接返回从UndetectedScraper获取的数据
            result_data = response["data"]
            logger.info(f"Successfully retrieved data: {result_data}")
            
            # 确保所有列表字段都是列表类型
            if isinstance(result_data, dict):
                for key in ["labels", "transactions", "related_addresses"]:
                    if key in result_data and not isinstance(result_data[key], list):
                        result_data[key] = list(result_data[key]) if result_data[key] else []
            
            return {
                "success": True,
                "data": result_data
            }
            
        except Exception as e:
            logger.error(f"Error fetching address info: {str(e)}")
            return {"success": False, "error": str(e)}

    def _extract_risk_score(self, soup: BeautifulSoup) -> Optional[int]:
        """Extract risk score from the page"""
        try:
            risk_element = soup.find('div', {'class': 'risk-score'})
            return int(risk_element.text) if risk_element else None
        except Exception as e:
            logger.error(f"Error extracting risk score: {str(e)}")
            return None

    def _extract_risk_level(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract risk level from the page"""
        try:
            risk_level_element = (
                soup.find('div', {'class': 'risk-level'}) or
                soup.find('span', {'class': 'risk-level'}) or
                soup.find('div', text=lambda t: t and 'Risk Level' in t)
            )
            if risk_level_element:
                if 'Risk Level' in risk_level_element.text:
                    return risk_level_element.find_next(text=True).strip()
                return risk_level_element.text.strip()
            return None
        except Exception as e:
            logger.error(f"Error extracting risk level: {str(e)}")
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
