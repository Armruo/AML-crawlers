# Redis 终端操作指南

## 1. 连接 Redis
```bash
# 本地连接
redis-cli

# 指定主机和端口连接
redis-cli -h hostname -p port

# 带密码连接
redis-cli -a password
```

## 2. 基本操作命令

### 键值操作
```bash
# 设置键值
SET key value
SET name "张三"

# 获取值
GET key
GET name

# 设置带过期时间的键值（秒）
SETEX key seconds value
SETEX session 3600 "user123"

# 删除键
DEL key
DEL name

# 检查键是否存在
EXISTS key
EXISTS name

# 查看键的剩余生存时间（秒）
TTL key
```

### 列表操作
```bash
# 向列表右端添加元素
RPUSH key value [value ...]
RPUSH tasks "任务1" "任务2"

# 向列表左端添加元素
LPUSH key value [value ...]
LPUSH tasks "紧急任务"

# 获取列表范围内的元素
LRANGE key start stop
LRANGE tasks 0 -1  # 获取所有元素

# 从左端弹出元素
LPOP key
LPOP tasks
```

### 哈希表操作
```bash
# 设置哈希表字段
HSET key field value
HSET user:1 name "张三"
HSET user:1 age "25"

# 获取哈希表字段
HGET key field
HGET user:1 name

# 获取所有字段和值
HGETALL key
HGETALL user:1
```

### 集合操作
```bash
# 添加集合成员
SADD key member [member ...]
SADD cities "北京" "上海" "广州"

# 获取集合所有成员
SMEMBERS key
SMEMBERS cities

# 判断元素是否是集合成员
SISMEMBER key member
SISMEMBER cities "北京"
```

## 3. 数据库操作
```bash
# 切换数据库（0-15）
SELECT index
SELECT 1

# 查看当前数据库的键数量
DBSIZE

# 清空当前数据库
FLUSHDB

# 清空所有数据库
FLUSHALL
```

## 4. 实用命令
```bash
# 查看所有键
KEYS pattern
KEYS *          # 所有键
KEYS user:*     # 以user:开头的键

# 查看服务器信息
INFO

# 监视键的操作
MONITOR

# 查看命令帮助
HELP command
HELP SET
```

## 5. 事务操作
```bash
# 开始事务
MULTI

# 执行命令（加入队列）
SET key1 "value1"
SET key2 "value2"

# 执行事务
EXEC

# 取消事务
DISCARD
```

## 6. 发布订阅
```bash
# 订阅频道
SUBSCRIBE channel [channel ...]
SUBSCRIBE news

# 发布消息
PUBLISH channel message
PUBLISH news "Hello World"
```

## 注意事项：
1. Redis 命令不区分大小写，但键名区分大小写
2. 在生产环境中请谨慎使用 FLUSHALL/FLUSHDB 命令
3. KEYS 命令在生产环境中要谨慎使用，因为它可能会阻塞服务器
4. 建议为重要数据设置过期时间
5. 在执行重要操作前先备份数据
