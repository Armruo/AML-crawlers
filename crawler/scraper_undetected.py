import logging
import time
import undetected_chromedriver as uc
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logger = logging.getLogger(__name__)

class UndetectedScraper:
    def __init__(self):
        self.base_url = "https://misttrack.io/aml_risks"
        self.setup_driver()

    def setup_driver(self):
        """设置Undetected ChromeDriver"""
        options = uc.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--window-size=1920,1080')
        
        self.driver = uc.Chrome(options=options)
        self.driver.implicitly_wait(10)

    def search_address(self, address):
        """使用Undetected ChromeDriver搜索地址"""
        try:
            url = f"{self.base_url}/{address}"
            logger.info(f"Searching address: {url}")
            
            self.driver.get(url)
            
            # 等待页面加载完成
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "body"))
            )
            
            # 等待一段时间让JavaScript执行完成
            time.sleep(5)
            
            # 滚动页面以触发懒加载
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            # 获取页面内容
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'lxml')
            
            # 提取所需信息
            result = {
                "address": address,
                "risk_score": self._extract_risk_score(soup),
                "labels": self._extract_labels(soup),
                "transactions": self._extract_transactions(soup),
                "related_addresses": self._extract_related_addresses(soup),
                "risk_analysis": self._extract_risk_analysis(soup)
            }
            
            logger.info(f"Extracted data for address {address}")
            return result
            
        except Exception as e:
            logger.error(f"Error searching address {address}: {str(e)}")
            return {"error": str(e)}
        
    def _extract_risk_score(self, soup):
        """提取风险分数"""
        try:
            # 尝试多个可能的选择器
            selectors = [
                'div.risk-score-value',
                'div[data-risk-score]',
                'div.risk-score',
                'span.risk-score'
            ]
            
            for selector in selectors:
                element = soup.select_one(selector)
                if element:
                    if selector == 'div[data-risk-score]':
                        return element.get('data-risk-score', 'N/A')
                    return element.text.strip()
            
            return "N/A"
        except Exception as e:
            logger.error(f"Error extracting risk score: {str(e)}")
            return "N/A"

    def _extract_labels(self, soup):
        """提取标签"""
        try:
            labels = []
            # 尝试多个可能的选择器
            selectors = [
                'div.label-tag',
                'span.label',
                'div.tag',
                'div.risk-label'
            ]
            
            for selector in selectors:
                elements = soup.select(selector)
                for element in elements:
                    label_text = element.text.strip()
                    if label_text and label_text not in labels:
                        labels.append(label_text)
            
            return labels
        except Exception as e:
            logger.error(f"Error extracting labels: {str(e)}")
            return []

    def _extract_transactions(self, soup):
        """提取交易记录"""
        try:
            transactions = []
            # 尝试多个可能的选择器
            tx_selectors = [
                'div.transaction-row',
                'tr.transaction',
                'div.tx-item',
                'div.transaction-item'
            ]
            
            for selector in tx_selectors:
                elements = soup.select(selector)
                for element in elements:
                    tx = {}
                    
                    # 尝试提取交易哈希
                    hash_selectors = ['div.tx-hash a', 'td.hash a', 'div.hash a', 'a.tx-hash']
                    for hash_selector in hash_selectors:
                        hash_element = element.select_one(hash_selector)
                        if hash_element:
                            tx['hash'] = hash_element.text.strip()
                            break
                    
                    # 尝试提取日期
                    date_selectors = ['div.tx-date', 'td.date', 'div.date', 'span.date']
                    for date_selector in date_selectors:
                        date_element = element.select_one(date_selector)
                        if date_element:
                            tx['date'] = date_element.text.strip()
                            break
                    
                    # 尝试提取金额
                    amount_selectors = ['div.tx-amount', 'td.amount', 'div.amount', 'span.amount']
                    for amount_selector in amount_selectors:
                        amount_element = element.select_one(amount_selector)
                        if amount_element:
                            tx['amount'] = amount_element.text.strip()
                            break
                    
                    if tx:  # 只有当至少有一个字段时才添加交易
                        transactions.append(tx)
            
            return transactions
        except Exception as e:
            logger.error(f"Error extracting transactions: {str(e)}")
            return []

    def _extract_related_addresses(self, soup):
        """提取相关地址"""
        try:
            addresses = []
            # 尝试多个可能的选择器
            selectors = [
                'div.related-address a',
                'div.address a',
                'td.address a',
                'a.address'
            ]
            
            for selector in selectors:
                elements = soup.select(selector)
                for element in elements:
                    address = element.text.strip()
                    if address and address not in addresses:  # 避免重复
                        addresses.append(address)
            
            return addresses
        except Exception as e:
            logger.error(f"Error extracting related addresses: {str(e)}")
            return []

    def _extract_risk_analysis(self, soup):
        """提取风险分析"""
        try:
            analysis = {}
            # 尝试多个可能的选择器
            selectors = [
                'div.risk-analysis-item',
                'div.risk-detail',
                'div.analysis-row',
                'div.risk-item'
            ]
            
            for selector in selectors:
                elements = soup.select(selector)
                for element in elements:
                    # 尝试提取类别
                    category_selectors = ['div.category', 'div.title', 'div.risk-type', 'div.type']
                    description_selectors = ['div.description', 'div.content', 'div.risk-detail', 'div.detail']
                    
                    category = None
                    description = None
                    
                    for cat_selector in category_selectors:
                        category_element = element.select_one(cat_selector)
                        if category_element:
                            category = category_element.text.strip()
                            break
                    
                    for desc_selector in description_selectors:
                        description_element = element.select_one(desc_selector)
                        if description_element:
                            description = description_element.text.strip()
                            break
                    
                    if category and description:
                        analysis[category] = description
            
            return analysis
        except Exception as e:
            logger.error(f"Error extracting risk analysis: {str(e)}")
            return {}

    def __del__(self):
        """清理资源"""
        try:
            if hasattr(self, 'driver'):
                self.driver.quit()
        except Exception as e:
            logger.error(f"Error cleaning up driver: {str(e)}")
