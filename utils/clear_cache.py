"""
清理 Redis 缓存的工具脚本
"""

import redis

def clear_cache():
    # 创建 Redis 连接
    redis_client = redis.Redis(
        host='localhost',
        port=6379,
        db=0,
        decode_responses=True
    )
    
    try:
        # 清空当前数据库
        redis_client.flushdb()
        print("Successfully cleared Redis cache")
        return True
    except Exception as e:
        print(f"Failed to clear Redis cache: {str(e)}")
        return False
    finally:
        redis_client.close()

if __name__ == "__main__":
    clear_cache()
