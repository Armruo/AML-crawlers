from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import time
import logging
from .validators import CryptoAddressValidator
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
import asyncio

logger = logging.getLogger(__name__)

class CrawlerViewSet(viewsets.ViewSet):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.validator = CryptoAddressValidator()

    def create(self, request, *args, **kwargs):
        serializer = CrawlerTaskSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        address = serializer.validated_data['address']
        network = serializer.validated_data['network']
        task_id = str(uuid.uuid4())

        # 验证地址格式
        is_valid, message, possible_coins = self.validator.validate(address)
        if not is_valid:
            return Response({"error": message}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # 使用 scraper_service 获取地址信息
            scraper_service = MistTrackScraperService(address=address, network=network)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(scraper_service.get_address_info())
            loop.close()

            if not result["success"]:
                self._send_ws_notification(task_id, "error", {"error": result["error"]})
                return Response({"error": result["error"]}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # 发送成功通知
            self._send_ws_notification(task_id, "completed", {
                "address": address,
                "result": result["data"]
            })

            return Response({
                "task_id": task_id,
                "status": "completed",
                "address": address,
                "result": result["data"]
            })

        except Exception as e:
            logger.error(f"Error processing request: {str(e)}")
            self._send_ws_notification(task_id, "error", {"error": str(e)})
            return Response(
                {"error": "Internal server error occurred"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _send_ws_notification(self, task_id: str, status: str, data: dict):
        """Send WebSocket notification"""
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "crawler_updates",
            {
                "type": "crawler_message",
                "message": {
                    "task_id": task_id,
                    "status": status,
                    "data": data
                }
            }
        )

    @action(detail=False, methods=['post'])
    def upload_file(self, request):
        """Handle file upload request"""
        serializer = FileUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        uploaded_file = request.FILES['file']
        network = request.data.get('network', 'ETH')  # 默认使用ETH网络
        if not network or network.lower() == 'undefined':
            network = 'ETH'
            logger.info(f"Using default network: {network}")
        task_id = str(uuid.uuid4())

        try:
            # Save file temporarily
            path = default_storage.save(f'tmp/{uploaded_file.name}', ContentFile(uploaded_file.read()))
            full_path = default_storage.path(path)

            # Try different encodings to read the file
            encodings_to_try = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'latin1']
            df = None
            
            for encoding in encodings_to_try:
                try:
                    df = pd.read_csv(full_path, encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue
                except Exception as e:
                    logger.error(f"Error reading CSV with encoding {encoding}: {str(e)}")
                    continue
            
            if df is None:
                return Response(
                    {"error": "Unable to read the file. Please ensure it's a valid CSV file with UTF-8 or GBK encoding."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Verify the 'address' column exists
            if 'address' not in df.columns:
                return Response(
                    {"error": "The CSV file must contain an 'address' column"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Clean the addresses
            addresses = df['address'].astype(str).str.strip().dropna().tolist()
            total_addresses = len(addresses)

            if not addresses:
                return Response(
                    {"error": "No valid addresses found in file"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Process addresses in batches
            batch_size = 5  # 每批处理5个地址
            results = []
            
            for i in range(0, len(addresses), batch_size):
                batch_addresses = addresses[i:i + batch_size]
                
                # Send progress update
                self._send_ws_notification(task_id, "processing", {
                    "progress": (i / total_addresses) * 100,
                    "current": i,
                    "total": total_addresses,
                    "processing": batch_addresses
                })

                # Process batch concurrently
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                batch_results = loop.run_until_complete(
                    MistTrackScraperService.process_addresses(batch_addresses, network)
                )
                loop.close()
                
                # Add results
                results.extend(batch_results)

            # Clean up temporary file
            default_storage.delete(path)

            # Send completion notification
            self._send_ws_notification(task_id, "completed", {
                "progress": 100,
                "results": results
            })

            return Response({
                "task_id": task_id,
                "results": results
            })

        except Exception as e:
            logger.error(f"Error processing file upload: {str(e)}")
            # Clean up temporary file if it exists
            try:
                default_storage.delete(path)
            except:
                pass
            return Response(
                {"error": f"Error processing file: {str(e)}"},
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
            return JsonResponse({"error": "Address is required"}, status=400)
            
        validator = CryptoAddressValidator()
        is_valid, message, possible_coins = validator.validate(address)
        
        return JsonResponse({
            "is_valid": is_valid,
            "message": message,
            "possible_coins": possible_coins,
            "normalized_address": validator.normalize_eth_address(address) if is_valid and any(coin in ['ETH', 'BSC', 'MATIC'] for coin in possible_coins) else address
        })
        
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        logger.error(f"Error validating address: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def search(request):
    """Search endpoint"""
    try:
        data = json.loads(request.body)
        query = data.get('query')
        
        if not query:
            return JsonResponse({"error": "Query is required"}, status=400)
            
        scraper_service = MistTrackScraperService()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(scraper_service.search(query))
        loop.close()

        if not result["success"]:
            return JsonResponse({"error": result["error"]}, status=500)

        return JsonResponse({"results": result["data"]})
        
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        logger.error(f"Error performing search: {str(e)}")
        return JsonResponse({"error": str(e)}, status=500)
