import re
import logging
from web3 import Web3

logger = logging.getLogger(__name__)

class CryptoAddressValidator:
    """加密货币地址验证器"""
    
    # 地址格式正则表达式
    PATTERNS = {
        'ETH': r'^0x[0-9a-fA-F]{40}$',
        'BSC': r'^0x[0-9a-fA-F]{40}$',
        'MATIC': r'^0x[0-9a-fA-F]{40}$',
        
        'SOL': r'^[1-9A-HJ-NP-Za-km-z]{32,44}$',
        
        'BTC': r'^(1|3)[1-9A-HJ-NP-Za-km-z]{25,34}$|^bc1[0-9A-Za-z]{39,59}$',
        'TRX': r'^T[123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz]{33}$'
    }
    
    def __init__(self):
        self.patterns = {coin: re.compile(pattern) for coin, pattern in self.PATTERNS.items()}
        self.web3 = Web3()
        
    def _check_eth_checksum(self, address):
        """验证ETH地址校验和"""
        try:
            # 检查地址是否符合校验和格式
            return self.web3.is_checksum_address(address)
        except Exception as e:
            logger.error(f"Error checking ETH checksum: {str(e)}")
            return False
            
    def _validate_eth_like(self, address, coin):
        """验证ETH类地址（包括BSC和MATIC）"""
        if not self.patterns[coin].match(address):
            return False
            
        # 如果地址是小写或大写，转换为校验和格式
        try:
            checksum_address = self.web3.to_checksum_address(address)
            return True
        except Exception:
            return False
            
    def validate(self, address):
        """验证地址格式并返回可能的币种列表"""
        if not address:
            return False, "Address cannot be empty", []
            
        matching_coins = []
        
        # 特殊处理ETH类地址
        eth_like_coins = ['ETH', 'BSC', 'MATIC']
        for coin in eth_like_coins:
            if self._validate_eth_like(address, coin):
                matching_coins.append(coin)
                
        # 处理其他币种
        for coin, pattern in self.patterns.items():
            if coin not in eth_like_coins and pattern.match(address):
                # SOL地址格式较为宽松，只有在没有其他匹配时才考虑
                if coin == 'SOL' and len(matching_coins) > 0:
                    continue
                matching_coins.append(coin)
        
        if not matching_coins:
            return False, "Invalid address format", []
            
        return True, "Valid address format", matching_coins
        
    def normalize_eth_address(self, address):
        """标准化ETH地址（转换为校验和格式）"""
        try:
            return self.web3.to_checksum_address(address)
        except Exception:
            return address
