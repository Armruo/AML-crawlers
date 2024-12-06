import logging
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import time

logger = logging.getLogger(__name__)

class PlaywrightScraper:
    def __init__(self):
        self.base_url = "https://light.misttrack.io"
        self.playwright = None
        self.browser = None
        self.setup_browser()

    def setup_browser(self):
        """设置Playwright浏览器"""
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=True,  # 无头模式
            args=['--no-sandbox']
        )

    def search_address(self, address, coin='ETH'):
        """使用Playwright搜索地址"""
        try:
            url = f"{self.base_url}/address/{coin}/{address}"
            logger.info(f"Searching address {address} for coin {coin}")
            
            # 创建新的页面上下文
            context = self.browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            )
            page = context.new_page()
            
            # 导航到目标页面
            page.goto(url, wait_until='networkidle')
            
            # 等待页面加载完成
            page.wait_for_selector('.container', timeout=20000)
            
            # 如果遇到Cloudflare验证，等待更长时间
            if "Checking if the site connection is secure" in page.content():
                logger.info("Detected Cloudflare check, waiting...")
                page.wait_for_timeout(10000)  # 等待10秒
            
            # 获取页面内容
            content = page.content()
            soup = BeautifulSoup(content, 'lxml')
            
            # 解析数据
            result = {
                "address": address,
                "coin": coin,
                "page_content": content[:500]  # 仅用于测试
            }
            
            # 关闭页面和上下文
            page.close()
            context.close()
            
            return result
            
        except Exception as e:
            logger.error(f"Error searching address with Playwright: {str(e)}")
            return {"error": str(e)}
        
    def __del__(self):
        """清理资源"""
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
