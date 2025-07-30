# 🚀 Company Intelligence Platform - LIVE!

[![Deployment Status](https://img.shields.io/badge/Deployment-Live-brightgreen)](https://company-intelligence-api.onrender.com/api/health)
[![Frontend Status](https://img.shields.io/badge/Frontend-Live-brightgreen)](https://company-intelligence-frontend.onrender.com)
[![API Docs](https://img.shields.io/badge/API-Documentation-blue)](https://company-intelligence-api.onrender.com/docs)

A professional, production-ready Company Intelligence Platform that provides comprehensive company research, AI-powered lookalike discovery, and sentiment analysis. Built with FastAPI, React, and deployed on Render.

## 🌐 **Live Application**

### **🔗 Production URLs:**
- **🎯 Main Application**: https://company-intelligence-frontend.onrender.com
- **🔧 API Backend**: https://company-intelligence-api.onrender.com
- **📚 API Documentation**: https://company-intelligence-api.onrender.com/docs
- **💚 Health Check**: https://company-intelligence-api.onrender.com/api/health

## ✨ **Features**

### **🔍 Company Research Engine**
- **Smart Company Lookup**: Domain and company name validation
- **AI-Powered Research**: Langflow integration for comprehensive data
- **Intelligent Caching**: AstraDB-powered cache with configurable freshness
- **Real-time Processing**: Live data from multiple research APIs
- **Comprehensive Metrics**: Financial data, hiring status, growth scores

### **🤖 AI-Powered Lookalike Discovery**
- **Similar Company Identification**: Find companies similar to your target
- **Multi-source Data**: Exa Search and Tavily Research integration
- **Smart Filtering**: Advanced algorithms for relevant matches
- **Scalable Processing**: Handle multiple company comparisons

### **📊 Sentiment Analysis**
- **News Sentiment**: Analyze recent company news and sentiment
- **Market Intelligence**: Track company perception and trends
- **Risk Assessment**: Identify potential opportunities and risks

### **🎨 Professional UI/UX**
- **Modern React Frontend**: Built with Material-UI components
- **Responsive Design**: Works seamlessly on all devices
- **Intuitive Navigation**: Tab-based interface for easy use
- **Real-time Feedback**: Loading states and error handling

### **🔧 Production-Ready Architecture**
- **RESTful API**: FastAPI with automatic OpenAPI documentation
- **Async Processing**: Non-blocking operations for optimal performance
- **Health Monitoring**: Comprehensive health checks and error handling
- **Security**: Environment-based configuration and input validation

### **🛍️ EnableMart WooCommerce Integration (Coming Soon)**
- **AI Product Recommendations**: Intelligent similarity-based product suggestions
- **Customer Behavior Analysis**: Advanced shopping pattern recognition
- **Cross-sell/Upsell Optimization**: Revenue-maximizing product recommendations
- **Real-time Personalization**: Dynamic product suggestions based on browsing behavior

## 🚀 **Quick Start**

### **🌐 Use the Live Application (Recommended)**
The application is already deployed and ready to use:
- **Main App**: https://company-intelligence-frontend.onrender.com
- **API Docs**: https://company-intelligence-api.onrender.com/docs

### **💻 Local Development Setup**

#### **Prerequisites**
- Python 3.11+
- Node.js 18+
- Git

#### **Backend Setup**
```bash
# Clone the repository
git clone https://github.com/RyvrImmersive/crm-abm.git
cd crm-abm

# Set up Python environment
cd backend
pip install -r requirements.txt

# Configure environment variables
cp ../.env.example .env
# Edit .env with your API keys

# Run the backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### **Frontend Setup**
```bash
# In a new terminal
cd frontend
npm install
npm start
```

#### **Docker Setup**
```bash
# Run the entire application
docker-compose up
```

### **🔑 Required Environment Variables**
```bash
# Database
ASTRA_DB_TOKEN=your_astra_db_token
ASTRA_DB_ENDPOINT=your_astra_db_endpoint

# AI Services
LANGFLOW_API_KEY=your_langflow_api_key
LANGFLOW_FLOW_URL=your_langflow_flow_url

# Research APIs (Optional)
EXA_API_KEY=your_exa_api_key
TAVILY_API_KEY=your_tavily_api_key
```

## 📚 **API Endpoints**

### **🔍 Company Research**
- `POST /api/research`: Research a company by domain or name
- `GET /api/health`: Health check endpoint
- `GET /docs`: Interactive API documentation

### **🤖 Lookalike Discovery**
- `POST /api/lookalike`: Find companies similar to a target company
- `GET /api/lookalike/{company_id}`: Get cached lookalike results

### **📊 Sentiment Analysis**
- `POST /api/sentiment`: Analyze company sentiment from news
- `GET /api/sentiment/{company_id}`: Get cached sentiment analysis

### **💾 Data Management**
- `GET /api/companies`: List all researched companies
- `GET /api/companies/{company_id}`: Get specific company data
- `DELETE /api/companies/{company_id}`: Delete company data

### **📈 Example API Usage**

#### **Research a Company**
```bash
curl -X POST "https://company-intelligence-api.onrender.com/api/research" \
  -H "Content-Type: application/json" \
  -d '{"input": "openai.com"}'
```

#### **Find Similar Companies**
```bash
curl -X POST "https://company-intelligence-api.onrender.com/api/lookalike" \
  -H "Content-Type: application/json" \
  -d '{"company_name": "OpenAI", "limit": 5}'
```

#### **Health Check**
```bash
curl "https://company-intelligence-api.onrender.com/api/health"
```

## 📊 **Architecture**

### **Backend (FastAPI)**
- **Framework**: FastAPI with async support
- **Database**: AstraDB (Cassandra) for scalable data storage
- **AI Integration**: Langflow for research workflows
- **APIs**: Exa Search, Tavily Research for data enrichment
- **Deployment**: Docker containers on Render

### **Frontend (React)**
- **Framework**: React 18 with Material-UI
- **State Management**: React hooks and context
- **Styling**: Material-UI components with custom theming
- **Deployment**: Static hosting on Render

### **Infrastructure**
- **Platform**: Render (Production)
- **Database**: AstraDB (Cloud Cassandra)
- **Monitoring**: Built-in health checks and logging
- **Security**: Environment-based secrets management

## 🔗 **Related Documentation**

- **[Deployment Summary](./DEPLOYMENT_SUMMARY.md)**: Complete deployment guide and troubleshooting
- **[Executive Summary](./EXECUTIVE_SUMMARY.md)**: Business overview and objectives
- **[Applications Portfolio](./APPLICATIONS_PORTFOLIO.md)**: Complete application ecosystem

## 📞 **Support**

- **Live API Documentation**: https://company-intelligence-api.onrender.com/docs
- **Health Status**: https://company-intelligence-api.onrender.com/api/health
- **GitHub Repository**: https://github.com/RyvrImmersive/crm-abm

---

**✨ Built with ❤️ by RyvrImmersive | Deployed on Render | Powered by AstraDB & Langflow**
