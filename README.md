# Clay-HubSpot Integration

A full-stack application for integrating Clay.com with HubSpot, allowing you to monitor company changes and update corresponding scores in HubSpot based on data fetched from Clay.

## Features
- Clay data integration with HubSpot
- Company data synchronization
- Scheduled updates
- Modern React frontend
- RESTful API
- Webhook handling

## Setup

### Backend
1. Clone the repository
2. Configure environment variables in `.env`
3. Install dependencies: `pip install -r requirements.txt`
4. Run the backend: `uvicorn src.langflow.api.main:app --reload`

### Frontend
1. Navigate to the frontend directory: `cd frontend`
2. Install dependencies: `npm install`
3. Run the frontend: `npm start`

### Docker
Alternatively, you can run the entire application with Docker:
`docker-compose up`

## API Endpoints

### Clay Endpoints
- `/api/clay/process-company`: Process a single company
- `/api/clay/process-companies`: Process multiple companies
- `/api/clay/company-news/{domain}`: Get company news
- `/api/clay/company-jobs/{domain}`: Get company jobs
- `/api/clay/company-funding/{domain}`: Get company funding
- `/api/clay/company-profile/{domain}`: Get company profile
- `/api/clay/sync-to-hubspot/{domain}`: Sync company data to HubSpot
- `/api/clay/create-hubspot-properties`: Create HubSpot properties

### HubSpot Endpoints
- `/api/hubspot/companies`: Get companies from HubSpot
- `/api/hubspot/companies/{company_id}`: Get a specific company
- `/api/hubspot/companies/search`: Search for companies

### Scheduler Endpoints
- `/api/scheduler/status`: Get scheduler status
- `/api/scheduler/start`: Start the scheduler

### Prerequisites
- Python 3.9+
- Node.js 16+
- AstraDB account
- API keys: Exa, Tavily, Langflow

### 1. Environment Setup
```bash
# Clone and setup environment
cp .env.example .env
# Edit .env with your API keys
```

### 2. Backend Launch
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Frontend Launch
```bash
cd frontend
npm install
npm start
```

### 4. Access Application
- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/health

## 🔧 Configuration

### Required Environment Variables
```env
# Database
ASTRA_DB_TOKEN=your_astra_token
ASTRA_DB_ENDPOINT=your_astra_endpoint

# AI APIs
EXA_API_KEY=your_exa_key
TAVILY_API_KEY=your_tavily_key
LANGFLOW_API_KEY=your_langflow_key
LANGFLOW_FLOW_URL=your_langflow_url

# Optional
DATA_FRESHNESS_DAYS=360
```

## 📖 Usage Examples

### Research a Company
1. Enter company name (e.g., "Tesla")
2. Enter domain (e.g., "tesla.com")
3. Click "Research Company"
4. View comprehensive business intelligence

### Find Similar Companies
1. Research a company first
2. Click "Find Similar Companies"
3. View lookalike companies with:
   - Similarity scores
   - Financial data (revenue, market cap)
   - Industry classification
   - Direct website links

## 🚢 Deployment

### Docker Deployment
```bash
docker-compose up -d
```

### Cloud Deployment
- **Backend**: Deploy to Render/Railway using `render.yaml`
- **Frontend**: Deploy to Netlify using `netlify.toml`
- **Environment**: Set all required environment variables

See [DEPLOYMENT_SUMMARY.md](DEPLOYMENT_SUMMARY.md) for detailed instructions.

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   React Frontend │────│  FastAPI Backend │────│    AstraDB      │
│   (Port 3000)    │    │   (Port 8000)    │    │   (Vector DB)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ├── Langflow API
                                ├── Exa Search API
                                └── Tavily Research API
```

## 🧪 Testing

### API Testing
```bash
# Health check
curl http://localhost:8000/api/health

# Research company
curl -X POST "http://localhost:8000/api/research" \
  -H "Content-Type: application/json" \
  -d '{"company_name": "Tesla", "domain_name": "tesla.com"}'
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open Pull Request

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: Check `/docs` endpoint when running
- **Issues**: Create GitHub issues for bugs/features
- **API Keys**: Ensure all required environment variables are set

---

**Built with ❤️ for comprehensive company intelligence and business research.**
