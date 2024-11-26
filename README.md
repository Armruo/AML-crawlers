# AML Crawlers

一个用于抓取和分析加密货币地址反洗钱风险信息的工具集。

## 功能特点

- 支持多个数据源的风险信息抓取
- 支持单个地址查询和批量导入
- 实时进度反馈（WebSocket）
- 支持CSV和Excel文件批量导入
- 风险评分和标签分析
- 相关交易追踪
- 关联地址分析

## 技术栈

### 后端
- Python 3.10+
- Django
- Django REST framework
- Django Channels
- Redis (WebSocket后端)
- BeautifulSoup4
- Pandas

### 前端
- Next.js
- TypeScript
- TailwindCSS
- WebSocket

## 安装步骤

1. 克隆仓库
```bash
git clone https://github.com/YOUR_USERNAME/aml-crawlers.git
cd aml-crawlers
```

2. 安装后端依赖
```bash
pip install -r requirements.txt
```

3. 安装前端依赖
```bash
cd frontend
npm install
```

4. 配置环境变量
```bash
cp .env.example .env
# 编辑.env文件，填入必要的配置信息
```

5. 启动Redis服务
```bash
sudo service redis-server start
```

6. 运行数据库迁移
```bash
python manage.py migrate
```

7. 启动开发服务器
```bash
# 后端
python manage.py runserver

# 前端（新终端）
cd frontend
npm run dev
```

## 使用说明

1. 单个地址查询
- 访问首页
- 在搜索框中输入加密货币地址
- 点击"查询"按钮

2. 批量导入
- 准备包含address列的CSV或Excel文件
- 点击"上传文件"按钮
- 选择文件并上传
- 等待处理完成

## API文档

### 主要端点

- `POST /api/crawler/`: 单个地址查询
- `POST /api/crawler/upload_file/`: 文件上传处理
- `WebSocket /ws/task/{task_id}/`: 任务进度监控

详细的API文档请参考 [API文档](docs/api.md)

## 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件
