import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time

logger = logging.getLogger(__name__)

class SeleniumScraper:
    def __init__(self):
        self.base_url = "https://misttrack.io/aml_risks"
        self.setup_driver()

    def setup_driver(self):
        """设置Chrome驱动"""
        options = Options()
        options.add_argument('--headless')  # 无头模式
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        options.add_argument('--disable-blink-features=AutomationControlled')  # 禁用自动化标记
        options.add_experimental_option('excludeSwitches', ['enable-automation'])  # 禁用自动化开关
        options.add_experimental_option('useAutomationExtension', False)  # 禁用自动化扩展
        
        # 添加额外的 Chrome 配置
        prefs = {
            'profile.default_content_setting_values': {
                'images': 2,  # 禁用图片加载以提高速度
                'javascript': 1,  # 启用 JavaScript
                'cookies': 1,  # 启用 cookies
            }
        }
        options.add_experimental_option('prefs', prefs)
        
        self.driver = webdriver.Chrome(options=options)
        self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': '''
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
            '''
        })
        self.driver.implicitly_wait(10)

    def search_address(self, address):
        """使用Selenium搜索地址"""
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
            
            # 如果遇到Cloudflare验证，等待更长时间
            if "Checking if the site connection is secure" in self.driver.page_source:
                logger.info("Detected Cloudflare check, waiting...")
                time.sleep(15)  # 等待Cloudflare验证完成
            
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
            element = soup.select_one('div.risk-score-value')
            return element.text.strip() if element else "N/A"
        except Exception as e:
            logger.error(f"Error extracting risk score: {str(e)}")
            return "N/A"

    def _extract_labels(self, soup):
        """提取标签"""
        try:
            labels = []
            elements = soup.select('div.label-tag')
            for element in elements:
                labels.append(element.text.strip())
            return labels
        except Exception as e:
            logger.error(f"Error extracting labels: {str(e)}")
            return []

    def _extract_transactions(self, soup):
        """提取交易记录"""
        try:
            transactions = []
            elements = soup.select('div.transaction-row')
            for element in elements:
                tx = {
                    "hash": element.select_one('div.tx-hash a').text.strip(),
                    "date": element.select_one('div.tx-date').text.strip() if element.select_one('div.tx-date') else "",
                    "amount": element.select_one('div.tx-amount').text.strip() if element.select_one('div.tx-amount') else ""
                }
                transactions.append(tx)
            return transactions
        except Exception as e:
            logger.error(f"Error extracting transactions: {str(e)}")
            return []

    def _extract_related_addresses(self, soup):
        """提取相关地址"""
        try:
            addresses = []
            elements = soup.select('div.related-address a')
            for element in elements:
                addresses.append(element.text.strip())
            return addresses
        except Exception as e:
            logger.error(f"Error extracting related addresses: {str(e)}")
            return []

    def _extract_risk_analysis(self, soup):
        """提取风险分析"""
        try:
            analysis = {}
            elements = soup.select('div.risk-analysis-item')
            for element in elements:
                category = element.select_one('div.category').text.strip()
                description = element.select_one('div.description').text.strip()
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
