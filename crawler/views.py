from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import cloudscraper
import json
import time
import logging
from .validators import CryptoAddressValidator
from bs4 import BeautifulSoup
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import pandas as pd
from .serializers import CrawlerTaskSerializer, FileUploadSerializer
from channels.layers import get_channel_layer
import uuid
from asgiref.sync import async_to_sync
from .services import MistTrackScraperService
import logging

logger = logging.getLogger(__name__)

class MistTrackScraper:
    def __init__(self):
        # self.base_url = "https://light.misttrack.io"
        self.base_url = "https://misttrack.io/aml_risks"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "application/json"
        }
        self.session = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'mobile': False
            }
        )
        self.validator = CryptoAddressValidator()

    def _make_request(self, url, method="GET", data=None, params=None):
        try:
            logger.debug(f"Making {method} request to {url}")
            if method == "GET":
                response = self.session.get(url, headers=self.headers, params=params)
            else:
                response = self.session.post(url, headers=self.headers, json=data)
            
            logger.debug(f"Response status code: {response.status_code}")
            
            # 特别处理403状态码，这可能是Cloudflare的验证
            if response.status_code == 403:
                logger.warning("Received 403 status code - might be Cloudflare verification")
                # 尝试重新创建scraper会话
                self.session = cloudscraper.create_scraper(
                    browser={
                        'browser': 'chrome',
                        'platform': 'windows',
                        'mobile': False
                    }
                )
                # 重试请求
                if method == "GET":
                    response = self.session.get(url, headers=self.headers, params=params)
                else:
                    response = self.session.post(url, headers=self.headers, json=data)
                logger.debug(f"Retry response status code: {response.status_code}")
            
            response.raise_for_status()
            return response
        except cloudscraper.exceptions.CloudflareChallengeError as e:
            logger.error(f"Cloudflare challenge error: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Request failed: {str(e)}")
            return None

    def get_address_info(self, address):
        """获取地址基本信息"""
        try:
            # 验证地址格式
            is_valid, message, possible_coins = self.validator.validate(address)
            if not is_valid:
                return {"error": message}

            # 返回基本信息
            result = {
                "address": address,
                "normalized_address": self.validator.normalize_eth_address(address) if any(coin in ['ETH', 'BSC', 'MATIC'] for coin in possible_coins) else address,
                "possible_coins": possible_coins,
                "is_valid": True,
                "validation_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            }
            
            logger.info(f"Address info for {address}: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error processing address {address}: {str(e)}")
            return {"error": str(e)}

    def search_address(self, address):
        try:
            # 构建地址查询URL
            search_url = f"{self.base_url}/{address}"
            logger.info(f"Searching address: {search_url}")
            response = self._make_request(search_url)
            
            if not response:
                return {"error": "Failed to fetch data from MistTrack"}

            # 解析响应
            soup = BeautifulSoup(response.text, 'lxml')
            logger.debug(f"Response HTML: {response.text[:500]}...")
            
            # 提取相关信息
            result = {
                "address": address,
                "risk_score": self._extract_risk_score(soup),
                "labels": self._extract_labels(soup),
                "transactions": self._extract_transactions(soup),
                "related_addresses": self._extract_related_addresses(soup),
                "risk_analysis": self._extract_risk_analysis(soup)
            }
            
            logger.info(f"Search result for {address}: {result}")
            return result
        except Exception as e:
            logger.error(f"Error processing address {address}: {str(e)}")
            return {"error": str(e)}

    def search_transaction(self, tx_hash):
        try:
            # 构建交易查询URL
            tx_url = f"{self.base_url}/tx/{tx_hash}"
            response = self._make_request(tx_url)
            
            if not response:
                return {"error": "Failed to fetch transaction data"}

            # 解析响应
            soup = BeautifulSoup(response.text, 'lxml')
            
            # 提取交易相关信息
            result = {
                "tx_hash": tx_hash,
                "from_address": self._extract_from_address(soup),
                "to_address": self._extract_to_address(soup),
                "amount": self._extract_amount(soup),
                "timestamp": self._extract_timestamp(soup),
                "risk_analysis": self._extract_risk_analysis(soup)
            }
            logger.info("search_transaction:", result)
            
            return result
        except Exception as e:
            logger.error(f"Error processing transaction {tx_hash}: {str(e)}")
            return {"error": str(e)}

    # 辅助方法用于提取具体信息
    def _extract_risk_score(self, soup):
        try:
            risk_element = soup.select_one('div.risk-score-value')
            if risk_element:
                return risk_element.text.strip()
            
            # 尝试其他可能的选择器
            risk_element = soup.select_one('div[data-risk-score]')
            if risk_element:
                return risk_element.get('data-risk-score', 'N/A')
                
            return "N/A"
        except Exception:
            return "N/A"

    def _extract_labels(self, soup):
        try:
            labels = []
            # 尝试多个可能的选择器
            label_elements = soup.select('div.label-tag, span.label, div.tag')
            for element in label_elements:
                label_text = element.text.strip()
                if label_text:
                    labels.append(label_text)
            return labels
        except Exception:
            return []

    def _extract_transactions(self, soup):
        try:
            transactions = []
            # 尝试多个可能的选择器
            tx_elements = soup.select('div.transaction-row, tr.transaction, div.tx-item')
            for element in tx_elements:
                tx = {}
                
                # 尝试多个可能的选择器来获取交易哈希
                hash_element = element.select_one('div.tx-hash a, td.hash a, div.hash a')
                if hash_element:
                    tx['hash'] = hash_element.text.strip()
                
                # 尝试获取日期
                date_element = element.select_one('div.tx-date, td.date, div.date')
                if date_element:
                    tx['date'] = date_element.text.strip()
                
                # 尝试获取金额
                amount_element = element.select_one('div.tx-amount, td.amount, div.amount')
                if amount_element:
                    tx['amount'] = amount_element.text.strip()
                
                if tx:  # 只有当至少有一个字段时才添加交易
                    transactions.append(tx)
            return transactions
        except Exception as e:
            logger.error(f"Error extracting transactions: {str(e)}")
            return []

    def _extract_related_addresses(self, soup):
        try:
            addresses = []
            # 尝试多个可能的选择器
            address_elements = soup.select('div.related-address a, div.address a, td.address a')
            for element in address_elements:
                address = element.text.strip()
                if address and address not in addresses:  # 避免重复
                    addresses.append(address)
            return addresses
        except Exception:
            return []

    def _extract_from_address(self, soup):
        try:
            element = soup.select_one('.from-address')
            return element.text.strip() if element else "N/A"
        except Exception:
            return "N/A"

    def _extract_to_address(self, soup):
        try:
            element = soup.select_one('.to-address')
            return element.text.strip() if element else "N/A"
        except Exception:
            return "N/A"

    def _extract_amount(self, soup):
        try:
            element = soup.select_one('.amount')
            return element.text.strip() if element else "N/A"
        except Exception:
            return "N/A"

    def _extract_timestamp(self, soup):
        try:
            element = soup.select_one('.timestamp')
            return element.text.strip() if element else "N/A"
        except Exception:
            return "N/A"

    def _extract_risk_analysis(self, soup):
        try:
            analysis = {}
            # 尝试多个可能的选择器
            analysis_elements = soup.select('div.risk-analysis-item, div.risk-detail, div.analysis-row')
            for element in analysis_elements:
                category_element = element.select_one('div.category, div.title, div.risk-type')
                description_element = element.select_one('div.description, div.content, div.risk-detail')
                
                if category_element and description_element:
                    category = category_element.text.strip()
                    description = description_element.text.strip()
                    if category and description:
                        analysis[category] = description
            return analysis
        except Exception:
            return {}

class CrawlerViewSet(viewsets.ViewSet):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.scraper_service = MistTrackScraperService()

    async def create(self, request):
        """Handle single URL crawling request"""
        serializer = CrawlerTaskSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        url = serializer.validated_data['url']
        task_id = str(uuid.uuid4())

        try:
            logger.info(f"Processing URL: {url}")
            result = await self.scraper_service.get_address_info(url)
            
            if not result["success"]:
                raise Exception(result["error"])

            response_data = {
                "task_id": task_id,
                "url": url,
                "status": "success",
                "result": result["data"]
            }
            
            # Send success notification through WebSocket
            await self._send_ws_notification(task_id, "success", response_data)
            logger.info(f"Successfully processed URL: {url}")
            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            error_msg = f"Error processing URL {url}: {str(e)}"
            logger.error(error_msg)
            # Send error notification through WebSocket
            await self._send_ws_notification(task_id, "error", {"error": str(e)})
            return Response(
                {"error": error_msg},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def _send_ws_notification(self, task_id: str, status: str, data: dict):
        """Send WebSocket notification"""
        try:
            channel_layer = get_channel_layer()
            await channel_layer.group_send(
                f"task_{task_id}",
                {
                    "type": "task_progress",
                    "message": {
                        "status": status,
                        "task_id": task_id,
                        **data
                    }
                }
            )
        except Exception as e:
            logger.error(f"Error sending WebSocket notification: {str(e)}")

    @action(detail=False, methods=['post'])
    async def upload_file(self, request):
        """Handle file upload request"""
        serializer = FileUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            file = request.FILES['file']
            task_id = str(uuid.uuid4())
            
            # Save file temporarily
            path = default_storage.save(f'uploads/{task_id}/{file.name}', ContentFile(file.read()))
            
            # Process file based on type
            if file.name.endswith('.csv'):
                df = pd.read_csv(path)
            elif file.name.endswith(('.xls', '.xlsx')):
                df = pd.read_excel(path)
            else:
                raise ValueError("Unsupported file format")

            # Process addresses from file
            results = []
            for address in df['address'].unique():
                result = await self.scraper_service.get_address_info(address)
                if result["success"]:
                    results.append({"address": address, **result["data"]})
                await self._send_ws_notification(task_id, "progress", {
                    "address": address,
                    "status": "success" if result["success"] else "error"
                })

            # Clean up
            default_storage.delete(path)
            
            response_data = {
                "task_id": task_id,
                "status": "success",
                "results": results
            }
            await self._send_ws_notification(task_id, "success", response_data)
            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            error_msg = f"Error processing file: {str(e)}"
            logger.error(error_msg)
            await self._send_ws_notification(task_id, "error", {"error": str(e)})
            return Response(
                {"error": error_msg},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

@csrf_exempt
@require_http_methods(["POST"])
def validate_address(request):
    """API endpoint for address validation"""
    try:
        data = json.loads(request.body)
        address = data.get('address')
        
        if not address:
            return JsonResponse({"error": "Address parameter is required"}, status=400)

        scraper = MistTrackScraper()
        result = scraper.get_address_info(address)
        
        if "error" in result:
            return JsonResponse(result, status=400)
            
        return JsonResponse(result)

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON data"}, status=400)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return JsonResponse({"error": "Internal server error"}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def search(request):
    try:
        data = json.loads(request.body)
        query = data.get('query')
        query_type = data.get('type', 'address')  # 默认为地址查询

        if not query:
            return JsonResponse({"error": "Query parameter is required"}, status=400)

        # 根据查询类型调用相应的方法
        scraper = MistTrackScraper()
        if query_type == 'address':
            result = scraper.search_address(query)
        elif query_type == 'transaction':
            result = scraper.search_transaction(query)
        else:
            return JsonResponse({"error": "Invalid query type"}, status=400)

        return JsonResponse(result)

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON data"}, status=400)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return JsonResponse({"error": "Internal server error"}, status=500)
