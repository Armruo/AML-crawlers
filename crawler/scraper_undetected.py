import logging
import time
import undetected_chromedriver as uc
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

logger = logging.getLogger(__name__)

class BrowserPool:
    def __init__(self, max_browsers=3):
        self.browsers = []
        self.max_browsers = max_browsers

    def get_browser(self):
        try:
            if not self.browsers:
                options = uc.ChromeOptions()
                options.add_argument('--headless')
                options.add_argument('--no-sandbox')
                options.add_argument('--disable-dev-shm-usage')
                options.add_argument('--window-size=1920,1080')
                options.add_argument('--disable-gpu')
                options.add_argument('--disable-extensions')
                options.page_load_strategy = 'eager'  # 不等待所有资源加载完成
                browser = uc.Chrome(options=options)
                browser.set_page_load_timeout(30)  # 页面加载超时时间
                browser.implicitly_wait(5)  # 减少隐式等待时间
                self.browsers.append(browser)
            return self.browsers.pop(0)
        except Exception as e:
            logger.error(f"Error creating browser: {str(e)}")
            raise

    def return_browser(self, browser):
        """安全地返回浏览器到池中"""
        try:
            if browser and len(self.browsers) < self.max_browsers:
                self.browsers.append(browser)
            else:
                self.quit_browser(browser)
        except Exception as e:
            logger.error(f"Error returning browser to pool: {str(e)}")
            self.quit_browser(browser)

    def quit_browser(self, browser):
        """安全地关闭浏览器"""
        try:
            if browser:
                browser.quit()
        except Exception as e:
            logger.error(f"Error quitting browser: {str(e)}")

class UndetectedScraper:
    def __init__(self):
        self.base_url = "https://misttrack.io/aml_risks"
        self.browser_pool = BrowserPool(max_browsers=3)
        self.driver = None

    def setup_driver(self):
        """设置Undetected ChromeDriver"""
        options = uc.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--window-size=1920,1080')
        
        self.driver = uc.Chrome(options=options)
        self.driver.set_page_load_timeout(30)  # 页面加载超时时间
        self.driver.implicitly_wait(5)  # 减少隐式等待时间

    def search_address(self, address):
        """使用Undetected ChromeDriver搜索地址"""
        browser_acquired = False
        try:
            # 从池中获取浏览器
            self.driver = self.browser_pool.get_browser()
            browser_acquired = True
            
            url = f"{self.base_url}/{address}"
            logger.info(f"Searching address: {url}")
            
            # 设置页面加载超时
            self.driver.set_page_load_timeout(30)
            self.driver.get(url)
            
            # 等待页面主体加载
            try:
                WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
            except TimeoutException:
                logger.warning("Timeout waiting for body to load, continuing anyway")
            
            # 等待loading消失
            try:
                WebDriverWait(self.driver, 15).until_not(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".el-loading-mask"))
                )
            except TimeoutException:
                logger.warning("Loading mask didn't disappear, continuing anyway")
            
            # 等待数据加载
            try:
                WebDriverWait(self.driver, 15).until(
                    lambda driver: driver.execute_script(
                        "return !!(window.__NUXT__?.state?.address?.addressInfo || window.__NUXT__?.state?.address)"
                    )
                )
            except TimeoutException:
                logger.warning("Timeout waiting for data, continuing with available data")
            
            # 滚动页面以触发懒加载，并等待内容更新
            self.driver.execute_script("""
                window.scrollTo(0, document.body.scrollHeight);
                return new Promise((resolve) => {
                    const observer = new MutationObserver((mutations, obs) => {
                        obs.disconnect();
                        resolve();
                    });
                    observer.observe(document.body, {
                        childList: true,
                        subtree: true,
                        attributes: true,
                        characterData: true
                    });
                    setTimeout(resolve, 1000);  // 最多等待1秒
                });
            """)
            
            # 获取页面内容
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'lxml')
            
            # 尝试从JavaScript状态中获取数据
            try:
                risk_data = self.driver.execute_script("""
                    return (
                        window.__NUXT__?.state?.address?.addressInfo ||
                        window.__NUXT__?.state?.address ||
                        window.__NUXT__?.state ||
                        window.__INITIAL_STATE__
                    );
                """)
                if risk_data:
                    logger.info("Successfully extracted risk data")
            except Exception as e:
                logger.error(f"Error extracting risk data from JavaScript: {str(e)}")
                risk_data = None
            
            # 提取表格数据
            table_data = self._extract_table_data(soup)
            
            # 提取所需信息
            result = {
                "address": address,
                "risk_score": self._extract_risk_score(soup),
                "risk_level": self._extract_risk_level(soup, risk_data),
                "risk_type": self._extract_risk_type(soup, risk_data),
                "address_labels": self._extract_address_labels(soup),
                "labels": self._extract_labels(soup),
                "transactions": self._extract_transactions(soup),
                "related_addresses": self._extract_related_addresses(soup),
                "table_data": table_data,  # 添加表格数据
                # "raw_html": page_source
            }
            
            # 如果表格数据存在，使用它来更新风险类型和标签
            if table_data:
                first_row = table_data[0]
                result["risk_type"] = first_row.get("Risk Type", "Unknown")
                result["address_labels"] = first_row.get("Address/Risk Label", "Unknown")
                result["volume"] = first_row.get("Volume(USD)/%", "Unknown")
            
            logger.info(f"Extracted data for address {address}")
            return result
            
        except Exception as e:
            logger.error(f"Error searching address {address}: {str(e)}")
            return {"error": str(e)}
        finally:
            # 只有在实际获取了浏览器的情况下才尝试返回
            if browser_acquired and self.driver:
                try:
                    self.browser_pool.return_browser(self.driver)
                except Exception as e:
                    logger.error(f"Error returning browser to pool: {str(e)}")
                self.driver = None

    def _extract_risk_score(self, soup):
        """提取风险分数"""
        try:
            # 尝试多个可能的选择器
            selectors = [
                'div.risk-score-value',
                'div[data-risk-score]',
                'div.risk-score',
                'span.risk-score',
                '.risk-score'  # 添加更通用的选择器
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

    def _extract_risk_level(self, soup, risk_data=None):
        """提取风险等级"""
        try:
            # 首先尝试从JavaScript数据中提取
            if risk_data:
                if isinstance(risk_data, dict):
                    # 尝试多个可能的键名
                    for key in ['riskLevel', 'risk_level', 'level', 'risk']:
                        if key in risk_data:
                            return str(risk_data[key])
            
            # 尝试多个可能的选择器
            selectors = [
                '.risk-level',
                '[data-risk-level]',
                'div.risk-level',
                'span.risk-level',
                '.risk-score',
                '[data-risk-score]'
            ]
            
            for selector in selectors:
                element = soup.select_one(selector)
                if element:
                    if selector == '[data-risk-level]':
                        return element.get('data-risk-level', 'Unknown')
                    return element.text.strip()
            
            # 尝试查找包含"Risk Level"文本的元素
            risk_level_element = soup.find(text=lambda t: t and 'Risk Level' in t)
            if risk_level_element:
                parent = risk_level_element.parent
                if parent:
                    # 尝试获取下一个兄弟元素的文本
                    next_sibling = parent.find_next_sibling()
                    if next_sibling:
                        return next_sibling.text.strip()
                    # 或者尝试获取父元素的下一个文本节点
                    next_text = parent.find_next(text=True)
                    if next_text:
                        return next_text.strip()
            
            # 尝试在表格中查找
            table = soup.find('table', class_='el-table__body')
            if table:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 2:
                        # 检查第一个单元格是否包含风险相关文本
                        if any(risk_text in cells[0].text.lower() for risk_text in ['risk', 'level', 'score']):
                            return cells[1].text.strip()
            
            return "Unknown"
        except Exception as e:
            logger.error(f"Error extracting risk level: {str(e)}")
            return "Unknown"

    def _extract_risk_type(self, soup, risk_data=None):
        """提取风险类型"""
        try:
            # 首先尝试从JavaScript数据中提取
            if risk_data:
                if isinstance(risk_data, dict):
                    # 尝试多个可能的键名
                    for key in ['riskType', 'risk_type', 'type', 'category']:
                        if key in risk_data:
                            return str(risk_data[key])
            
            # 尝试从表格中提取
            table = soup.find('table', class_='el-table__body')
            if table:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 1:
                        risk_type_text = cells[0].get_text(strip=True)
                        if risk_type_text and risk_type_text.lower() != 'risk type':
                            return risk_type_text
            
            # 尝试多个可能的选择器
            selectors = [
                '.risk-type',
                '.risk-category',
                '[data-risk-type]',
                'div.risk-type',
                'span.risk-type',
                'td.el-table_1_column_1'  # 特定的表格列选择器
            ]
            
            for selector in selectors:
                elements = soup.select(selector)
                for element in elements:
                    if selector == '[data-risk-type]':
                        risk_type = element.get('data-risk-type')
                    else:
                        risk_type = element.text.strip()
                    if risk_type and risk_type.lower() != 'risk type':
                        return risk_type
            
            # 尝试查找包含"Risk Type"文本的元素
            risk_type_element = soup.find(text=lambda t: t and 'Risk Type' in t)
            if risk_type_element:
                parent = risk_type_element.parent
                if parent:
                    # 尝试获取下一个兄弟元素的文本
                    next_sibling = parent.find_next_sibling()
                    if next_sibling:
                        return next_sibling.text.strip()
                    # 或者尝试获取父元素的下一个文本节点
                    next_text = parent.find_next(text=True)
                    if next_text:
                        return next_text.strip()
            
            return "Unknown"
        except Exception as e:
            logger.error(f"Error extracting risk type: {str(e)}")
            return "Unknown"

    def _extract_address_labels(self, soup):
        """提取地址标签"""
        try:
            labels = []
            # 尝试多个可能的选择器
            selectors = [
                '.address-label',
                '.address-tag',
                '[data-address-label]',
                'div.address-label',
                'span.address-label'
            ]
            
            for selector in selectors:
                elements = soup.select(selector)
                if elements:
                    for element in elements:
                        if selector == '[data-address-label]':
                            label = element.get('data-address-label')
                        else:
                            label = element.text.strip()
                        if label:
                            labels.append(label)
            
            # 尝试查找包含"Address Label"或"Risk Label"文本的元素
            label_elements = soup.find_all(text=lambda t: t and ('Address Label' in t or 'Risk Label' in t))
            for label_element in label_elements:
                parent = label_element.parent
                if parent:
                    # 尝试获取下一个兄弟元素的文本
                    next_sibling = parent.find_next_sibling()
                    if next_sibling:
                        label = next_sibling.text.strip()
                        if label:
                            labels.append(label)
                    # 或者尝试获取父元素的下一个文本节点
                    next_text = parent.find_next(text=True)
                    if next_text:
                        label = next_text.strip()
                        if label:
                            labels.append(label)
            
            return list(set(labels))  # 去重
        except Exception as e:
            logger.error(f"Error extracting address labels: {str(e)}")
            return []

    def _extract_labels(self, soup):
        """提取标签"""
        try:
            labels = []
            # 尝试多个可能的选择器
            selectors = [
                '.label-tag',
                '.label',
                '.tag',
                '.risk-label',
                '[data-label]'
            ]
            
            for selector in selectors:
                elements = soup.select(selector)
                if elements:
                    labels.extend([el.text.strip() for el in elements if el.text.strip()])
            
            return list(set(labels))  # 去重
        except Exception as e:
            logger.error(f"Error extracting labels: {str(e)}")
            return []

    def _extract_transactions(self, soup):
        """提取交易信息"""
        try:
            transactions = []
            # 尝试多个可能的选择器
            selectors = [
                '.transaction-item',
                '.transaction',
                '.tx-item',
                '[data-transaction]'
            ]
            
            for selector in selectors:
                elements = soup.select(selector)
                for el in elements:
                    tx = {}
                    # 提取交易哈希
                    hash_el = el.select_one('.tx-hash, .hash, [data-hash]')
                    if hash_el:
                        tx['hash'] = hash_el.text.strip()
                    # 提取金额
                    amount_el = el.select_one('.amount, .value, [data-amount]')
                    if amount_el:
                        tx['amount'] = amount_el.text.strip()
                    # 提取时间戳
                    time_el = el.select_one('.timestamp, .time, [data-time]')
                    if time_el:
                        tx['timestamp'] = time_el.text.strip()
                    
                    if tx:  # 只有当提取到信息时才添加
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
                '.related-address',
                '.address-item',
                '[data-address]',
                'a[href*="address"]'  # 包含address的链接
            ]
            
            for selector in selectors:
                elements = soup.select(selector)
                for el in elements:
                    addr = el.get('data-address', el.text.strip())
                    if addr and len(addr) > 10:  # 简单的地址长度验证
                        addresses.append(addr)
            
            return list(set(addresses))  # 去重
        except Exception as e:
            logger.error(f"Error extracting related addresses: {str(e)}")
            return []

    def _extract_table_data(self, soup):
        """提取表格数据"""
        try:
            table_data = []
            table = soup.find('table', class_='el-table__body')
            if table:
                rows = table.find_all('tr', class_='el-table__row')
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 3:
                        risk_type = cells[0].get_text(strip=True)
                        label = cells[1].get_text(strip=True)
                        volume = cells[2].get_text(strip=True)
                        
                        table_data.append({
                            "Risk Type": risk_type,
                            "Address/Risk Label": label,
                            "Volume(USD)/%": volume
                        })
            return table_data
        except Exception as e:
            logger.error(f"Error extracting table data: {str(e)}")
            return []

    def __del__(self):
        """清理资源"""
        try:
            if hasattr(self, 'driver'):
                self.driver.quit()
        except Exception as e:
            logger.error(f"Error cleaning up driver: {str(e)}")
