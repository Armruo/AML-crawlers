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
        self.scraper_service = MistTrackScraperService()
        self.validator = CryptoAddressValidator()

    def create(self, request):
        """Handle single URL crawling request"""
        serializer = CrawlerTaskSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        address = serializer.validated_data['address']
        task_id = str(uuid.uuid4())

        # 验证地址格式
        is_valid, message, possible_coins = self.validator.validate(address)
        if not is_valid:
            return Response({"error": message}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # 使用 scraper_service 获取地址信息
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.scraper_service.get_address_info(address))
            loop.close()

            if not result["success"]:
                self._send_ws_notification(task_id, "error", {"error": result["error"]})
                return Response({"error": result["error"]}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # 发送WebSocket通知
            self._send_ws_notification(task_id, "completed", result["data"])
            return Response({
                "task_id": task_id,
                "status": "completed",
                "data": result["data"]
            })

        except Exception as e:
            logger.error(f"Error processing address {address}: {str(e)}")
            self._send_ws_notification(task_id, "error", {"error": str(e)})
            return Response(
                {"error": f"Error processing address: {str(e)}"},
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
        task_id = str(uuid.uuid4())

        try:
            # Save file temporarily
            path = default_storage.save(f'tmp/{uploaded_file.name}', ContentFile(uploaded_file.read()))
            full_path = default_storage.path(path)

            # Read addresses from file
            df = pd.read_csv(full_path)
            addresses = df['address'].tolist() if 'address' in df.columns else []

            if not addresses:
                return Response(
                    {"error": "No addresses found in file"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Process addresses
            results = []
            for address in addresses:
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    result = loop.run_until_complete(self.scraper_service.get_address_info(address))
                    loop.close()

                    if result["success"]:
                        results.append({
                            "address": address,
                            "status": "success",
                            "data": result["data"]
                        })
                    else:
                        results.append({
                            "address": address,
                            "status": "error",
                            "error": result["error"]
                        })
                except Exception as e:
                    results.append({
                        "address": address,
                        "status": "error",
                        "error": str(e)
                    })

            # Clean up
            default_storage.delete(path)

            # Send final results
            self._send_ws_notification(task_id, "completed", {"results": results})
            return Response({
                "task_id": task_id,
                "status": "completed",
                "data": {"results": results}
            })

        except Exception as e:
            logger.error(f"Error processing file: {str(e)}")
            self._send_ws_notification(task_id, "error", {"error": str(e)})
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
