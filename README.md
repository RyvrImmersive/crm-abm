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
- `/api/scheduler/stop`: Stop the scheduler
- `/api/scheduler/add-task`: Add a task
- `/api/scheduler/remove-task/{task_id}`: Remove a task

## Deployment to Render

This application is configured to be deployed to Render using the `render.yaml` file in the root directory of the project.

### Steps to Deploy

1. Push your code to a GitHub repository
2. Create a new Render account or log in to your existing account
3. Create a new Blueprint instance and connect it to your GitHub repository
4. Render will automatically detect the `render.yaml` file and create the necessary services:
   - `clay-hubspot-api`: The backend API service
   - `clay-hubspot-frontend`: The frontend React application
5. Set up the required environment variables in the Render dashboard

### Environment Variables

Make sure to set the following environment variables in the Render dashboard:

#### Backend
- `HUBSPOT_API_KEY`: Your HubSpot API key
- `CLAY_API_KEY`: Your Clay API key
- `FRONTEND_URL`: The URL of your frontend (e.g., `https://clay-hubspot-frontend.onrender.com`)

#### Frontend
- `REACT_APP_API_URL`: The URL of your backend API (e.g., `https://clay-hubspot-api.onrender.com/api`)
