"""
Redis 操作指南
这个模块提供了常用的 Redis 操作示例和工具函数
"""

import redis
from typing import Union, List, Dict, Any
import json

class RedisManager:
    def __init__(self, host='localhost', port=6379, db=0, password=None):
        """
        初始化 Redis 连接
        :param host: Redis 服务器地址
        :param port: Redis 端口
        :param db: 数据库编号
        :param password: Redis 密码
        """
        self.redis_client = redis.Redis(
            host=host,
            port=port,
            db=db,
            password=password,
            decode_responses=True  # 自动将字节解码为字符串
        )

    def set_value(self, key: str, value: Union[str, dict, list], expire: int = None) -> bool:
        """
        设置键值对
        :param key: 键名
        :param value: 值（支持字符串、字典、列表）
        :param expire: 过期时间（秒）
        :return: 是否成功
        """
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False)
            self.redis_client.set(key, value)
            if expire:
                self.redis_client.expire(key, expire)
            return True
        except Exception as e:
            print(f"设置值失败: {str(e)}")
            return False

    def get_value(self, key: str, return_type: str = 'str') -> Union[str, dict, list, None]:
        """
        获取值
        :param key: 键名
        :param return_type: 返回类型 ('str', 'dict', 'list')
        :return: 值
        """
        try:
            value = self.redis_client.get(key)
            if value is None:
                return None
            
            if return_type in ('dict', 'list'):
                return json.loads(value)
            return value
        except Exception as e:
            print(f"获取值失败: {str(e)}")
            return None

    def delete_key(self, key: str) -> bool:
        """
        删除键
        :param key: 键名
        :return: 是否成功
        """
        return bool(self.redis_client.delete(key))

    def list_push(self, key: str, *values: str) -> bool:
        """
        向列表推入数据
        :param key: 列表键名
        :param values: 要推入的值
        :return: 是否成功
        """
        try:
            self.redis_client.rpush(key, *values)
            return True
        except Exception as e:
            print(f"推入列表失败: {str(e)}")
            return False

    def list_pop(self, key: str) -> str:
        """
        从列表弹出数据
        :param key: 列表键名
        :return: 弹出的值
        """
        return self.redis_client.lpop(key)

    def hash_set(self, name: str, key: str, value: str) -> bool:
        """
        设置哈希表字段
        :param name: 哈希表名称
        :param key: 字段名
        :param value: 字段值
        :return: 是否成功
        """
        try:
            self.redis_client.hset(name, key, value)
            return True
        except Exception as e:
            print(f"设置哈希表失败: {str(e)}")
            return False

    def hash_get(self, name: str, key: str) -> str:
        """
        获取哈希表字段
        :param name: 哈希表名称
        :param key: 字段名
        :return: 字段值
        """
        return self.redis_client.hget(name, key)

    def hash_getall(self, name: str) -> Dict[str, str]:
        """
        获取哈希表所有字段
        :param name: 哈希表名称
        :return: 字段字典
        """
        return self.redis_client.hgetall(name)

    def set_add(self, key: str, *values: str) -> bool:
        """
        向集合添加元素
        :param key: 集合键名
        :param values: 要添加的值
        :return: 是否成功
        """
        try:
            self.redis_client.sadd(key, *values)
            return True
        except Exception as e:
            print(f"添加到集合失败: {str(e)}")
            return False

    def set_members(self, key: str) -> List[str]:
        """
        获取集合所有成员
        :param key: 集合键名
        :return: 成员列表
        """
        return list(self.redis_client.smembers(key))

    def key_exists(self, key: str) -> bool:
        """
        检查键是否存在
        :param key: 键名
        :return: 是否存在
        """
        return bool(self.redis_client.exists(key))

    def get_ttl(self, key: str) -> int:
        """
        获取键的剩余生存时间
        :param key: 键名
        :return: 剩余秒数（-1表示永久，-2表示不存在）
        """
        return self.redis_client.ttl(key)

    def flush_db(self) -> bool:
        """
        清空当前数据库
        :return: 是否成功
        """
        try:
            self.redis_client.flushdb()
            return True
        except Exception as e:
            print(f"清空数据库失败: {str(e)}")
            return False

# 使用示例
if __name__ == "__main__":
    # 创建 Redis 管理器实例
    redis_manager = RedisManager(host='localhost', port=6379, db=0)
    
    # 字符串操作示例
    redis_manager.set_value("name", "张三", expire=3600)  # 设置字符串，1小时后过期
    name = redis_manager.get_value("name")
    print(f"获取名字: {name}")

    # 字典操作示例
    user_info = {"name": "张三", "age": 25, "city": "北京"}
    redis_manager.set_value("user:1", user_info)
    user = redis_manager.get_value("user:1", return_type='dict')
    print(f"获取用户信息: {user}")

    # 列表操作示例
    redis_manager.list_push("tasks", "任务1", "任务2", "任务3")
    task = redis_manager.list_pop("tasks")
    print(f"获取任务: {task}")

    # 哈希表操作示例
    redis_manager.hash_set("user:2", "name", "李四")
    redis_manager.hash_set("user:2", "age", "30")
    user_data = redis_manager.hash_getall("user:2")
    print(f"获取用户哈希表: {user_data}")

    # 集合操作示例
    redis_manager.set_add("cities", "北京", "上海", "广州")
    cities = redis_manager.set_members("cities")
    print(f"获取城市集合: {cities}")
