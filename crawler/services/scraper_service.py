import logging
import asyncio
import concurrent.futures
from typing import Dict, Any, List, Optional
from bs4 import BeautifulSoup
from ..scraper_undetected import UndetectedScraper
from ..cache_manager import CacheManager
from ..validators import CryptoAddressValidator

logger = logging.getLogger(__name__)

class MistTrackScraperService:
    def __init__(self, address: str, network: str = 'ETH'):
        self.address = address
        self.network = network if network and network.lower() != 'undefined' else 'ETH'
        self.base_url = f"https://misttrack.io/aml_risks/{self.network}/{self.address}"
        self.validator = CryptoAddressValidator()
        self.scraper = None  # 延迟初始化
        self.cache_manager = CacheManager()

    def _get_scraper(self):
        """延迟初始化爬虫实例"""
        if self.scraper is None:
            self.scraper = UndetectedScraper()
        return self.scraper

    @classmethod
    async def process_addresses(cls, addresses: List[str], network: str = 'ETH') -> List[Dict[str, Any]]:
        """并发处理多个地址"""
        tasks = []
        for address in addresses:
            service = cls(address=address, network=network)
            tasks.append(service.get_address_info())
        
        return await asyncio.gather(*tasks)

    async def get_address_info(self) -> Dict[str, Any]:
        """获取地址信息"""
        logger.info(f"Getting info for address {self.address} on network {self.network}")
        
        # 验证地址格式
        valid, message, _ = self.validator.validate(self.address)
        if not valid:
            logger.error(f"Invalid address format: {self.address}")
            return {"success": False, "error": message}

        try:
            # 检查缓存
            cached_result = self.cache_manager.get_cached_result(self.address, self.network)
            if cached_result:
                logger.info(f"Cache hit for {self.address} on {self.network}")
                logger.info(f"Using cached result for {self.address}: {cached_result}")
                return {"success": True, "data": cached_result}

            # 如果没有缓存，爬取数据
            logger.info(f"Making request for address {self.address}")
            result = await self._make_request(self.base_url)
            
            # 缓存结果
            if result["success"]:
                self.cache_manager.cache_result(self.address, self.network, result["data"])
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting address info: {str(e)}")
            return {"success": False, "error": str(e)}

    async def _make_request(self, url: str) -> Dict[str, Any]:
        """使用线程池执行同步的爬虫操作"""
        try:
            loop = asyncio.get_event_loop()
            with concurrent.futures.ThreadPoolExecutor() as pool:
                result = await loop.run_in_executor(
                    pool,
                    self._get_scraper().search_address,  # 使用延迟初始化的爬虫
                    f"{self.network}/{self.address}"
                )
            
            if "error" in result:
                return {"success": False, "error": result["error"]}
            
            return {"success": True, "data": result}
            
        except Exception as e:
            logger.error(f"Error making request: {str(e)}")
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
