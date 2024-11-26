import logging
import requests
from crawler.views import MistTrackScraper

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_crawler.log')
    ]
)

logger = logging.getLogger(__name__)

def test_website_accessibility():
    """测试网站可访问性"""
    try:
        response = requests.get("https://misttrack.io")
        logger.info(f"Website status code: {response.status_code}")
        logger.info(f"Website headers: {response.headers}")
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Error accessing website: {str(e)}")
        return False

def test_address_validation():
    """测试地址验证功能"""
    test_addresses = {
        # 有效地址
        'ETH': '0x28c6c06298d514db089934071355e5743bf21d60',
        'BSC': '0x28c6c06298d514db089934071355e5743bf21d60',
        'MATIC': '0x28c6c06298d514db089934071355e5743bf21d60',
        'BTC': '1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa',
        'TRX': 'TF5Bn4cJCT6GVeUgyCN9qCzdH1RcnnK8yF',
        'LTC': 'LVg2kJoFNg45Nbpy53h7Fe1wKyeXVRhMH9',
        'DOGE': 'D8gfxKyWN56c8VWZt7XHZxLhDMUjB8wBgk',
        'XRP': 'rMQ98K56yXJbDGv49ZSmW51sLn94Xe1mu1',
        'SOL': '2wmVCSfPxGPjrnMMn7rchp4uaeoTqN39mXFC2zhPdri9',
        # 无效地址
        'INVALID': 'invalid_address',
        'INVALID_ETH': '0xinvalid',
        'EMPTY': ''
    }

    scraper = MistTrackScraper()
    
    for coin, address in test_addresses.items():
        logger.info(f"\nTesting {coin} address: {address}")
        result = scraper.get_address_info(address)
        logger.info(f"Validation result: {result}")
        
        if "error" in result:
            logger.warning(f"Validation failed: {result['error']}")
        else:
            logger.info(f"Address is valid. Detected coin: {result['coin']}")
            logger.info(f"Possible coins: {result['possible_coins']}")

def test_address_checksum():
    """测试地址校验和验证"""
    eth_addresses = [
        # 有效的校验和地址
        '0x5aAeb6053F3E94C9b9A09f33669435E7Ef1BeAed',
        # 无效的校验和地址（大小写错误）
        '0x5aaeb6053f3e94c9b9a09f33669435e7ef1beaed',
        # 完全无效的地址
        '0x5aAeb6053F3E94C9b9A09f33669435E7Ef1BeAe',
    ]

    scraper = MistTrackScraper()
    
    for address in eth_addresses:
        logger.info(f"\nTesting ETH address checksum: {address}")
        result = scraper.get_address_info(address)
        logger.info(f"Validation result: {result}")

def test_search_address():
    """测试地址搜索"""
    address = "0x28c6c06298d514db089934071355e5743bf21d60"
    
    scraper = MistTrackScraper()
    result = scraper.search_address(address)
    logger.info(f"Search result for {address}: {result}")
    
    
def main():
    """主测试函数"""
    logger.info("Starting tests...")
    
    if not test_website_accessibility():
        logger.error("Website is not accessible")
        return

    # test_address_validation()
    
    # test_address_checksum()
    
    test_search_address()

if __name__ == "__main__":
    main()
