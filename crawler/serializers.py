from rest_framework import serializers
import logging
import re

logger = logging.getLogger(__name__)

class EthereumAddressField(serializers.Field):
    def to_internal_value(self, value):
        # 验证以太坊地址格式
        if not re.match(r'^0x[a-fA-F0-9]{40}$', value):
            logger.error(f"Invalid Ethereum address format: {value}")
            raise serializers.ValidationError("Invalid Ethereum address format")
        return value

    def to_representation(self, value):
        return value

class CrawlerTaskSerializer(serializers.Serializer):
    url = EthereumAddressField()
    status = serializers.CharField(read_only=True)
    result = serializers.JSONField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)

    def validate_url(self, value):
        if not value:
            logger.error("Ethereum address is required")
            raise serializers.ValidationError("Ethereum address is required")
        return value

class FileUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    
    def validate_file(self, value):
        if not value:
            logger.error("File is required")
            raise serializers.ValidationError("File is required")
            
        # 检查文件大小（限制为10MB）
        if value.size > 10 * 1024 * 1024:
            logger.error(f"File size {value.size} exceeds limit")
            raise serializers.ValidationError("File size should not exceed 10MB")
            
        # 检查文件类型
        allowed_types = ['text/csv', 'application/vnd.ms-excel', 
                        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet']
        if value.content_type not in allowed_types:
            logger.error(f"Invalid file type: {value.content_type}")
            raise serializers.ValidationError("Only CSV and Excel files are allowed")
            
        return value
