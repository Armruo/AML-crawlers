# AML Crawlers

A comprehensive toolkit for crawling and analyzing anti-money laundering (AML) risk information associated with cryptocurrency addresses.

## Features

- Multi-source risk information crawling
- Single address query and batch import support
- Real-time progress feedback (WebSocket)
- CSV and Excel file batch processing
- Risk scoring and tag analysis
- Transaction tracking
- Related address analysis

## Tech Stack

### Backend
- Python 3.10+
- Django
- Django REST framework
- Django Channels
- Redis (WebSocket backend)
- BeautifulSoup4
- Pandas

### Frontend
- Next.js
- TypeScript
- TailwindCSS
- WebSocket

## Installation

1. Clone the repository
```bash
git clone https://github.com/Armruo/AML-crawlers.git
cd AML-crawlers
```

2. Install backend dependencies
```bash
pip install -r requirements.txt
```

3. Install frontend dependencies
```bash
cd frontend
npm install
```

4. Configure environment variables
```bash
cp .env.template .env
# Edit the .env file with your configuration
```

5. Start Redis server
```bash
sudo service redis-server start
```

6. Run database migrations
```bash
python manage.py migrate
```

7. Start development servers
```bash
# Backend
python manage.py runserver

# Frontend (in a new terminal)
cd frontend
npm run dev
```

## Usage

### Single Address Query
1. Navigate to the homepage
2. Enter a cryptocurrency address in the search box
3. Click the "Search" button

### Batch Import
1. Prepare a CSV or Excel file with an 'address' column
2. Click the "Upload File" button
3. Select and upload your file
4. Monitor the processing progress

## API Documentation

### Main Endpoints

- `POST /api/crawler/`: Single address query
- `POST /api/crawler/upload_file/`: File upload processing
- `WebSocket /ws/task/{task_id}/`: Task progress monitoring

For detailed API documentation, please refer to [API Documentation](docs/api.md)

## Contributing

1. Fork the project
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details

## Acknowledgments

- Thanks to all the contributors who have helped with this project
- Special thanks to the open-source community for their invaluable tools and libraries
