import logging
import time
from crawler.scraper_selenium import SeleniumScraper
from crawler.scraper_playwright import PlaywrightScraper
from crawler.scraper_undetected import UndetectedScraper
from crawler.scraper_proxy import ProxyScraper

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_selenium():
    """测试Selenium爬虫"""
    logger.info("Testing Selenium Scraper...")
    scraper = SeleniumScraper()
    result = scraper.search_address("0x28c6c06298d514db089934071355e5743bf21d60")
    logger.info(f"Selenium result: {result}")

def test_playwright():
    """测试Playwright爬虫"""
    logger.info("Testing Playwright Scraper...")
    scraper = PlaywrightScraper()
    result = scraper.search_address("0x28c6c06298d514db089934071355e5743bf21d60")
    logger.info(f"Playwright result: {result}")

def test_undetected():
    """测试Undetected-ChromeDriver爬虫"""
    logger.info("Testing Undetected-ChromeDriver Scraper...")
    scraper = UndetectedScraper()
    result = scraper.search_address("0x28c6c06298d514db089934071355e5743bf21d60")
    logger.info(f"Undetected-ChromeDriver result: {result}")

def test_proxy():
    """测试代理IP池爬虫"""
    logger.info("Testing Proxy Scraper...")
    scraper = ProxyScraper()
    result = scraper.search_address("0x28c6c06298d514db089934071355e5743bf21d60")
    logger.info(f"Proxy result: {result}")

def main():
    """主测试函数"""
    logger.info("Starting scraper tests...")
    
    # 测试所有爬虫实现
    test_undetected()
    time.sleep(2)
    
    # test_selenium()
    # time.sleep(2)  # 等待一段时间再测试下一个
    
    # test_playwright()
    # time.sleep(2)
    
    # test_proxy()

if __name__ == "__main__":
    main()
