import axios from 'axios';

// Create an axios instance with default config
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Clay API endpoints
export const clayApi = {
  // Process a single company
  processCompany: (domain) => {
    return api.post('/clay/process-company', { domain });
  },
  
  // Process multiple companies
  processCompanies: (domains, forceUpdate = false) => {
    return api.post('/clay/process-companies', { domains, force_update: forceUpdate });
  },
  
  // Get company news
  getCompanyNews: (domain) => {
    return api.get(`/clay/company-news/${domain}`);
  },
  
  // Get company jobs
  getCompanyJobs: (domain) => {
    return api.get(`/clay/company-jobs/${domain}`);
  },
  
  // Get company funding
  getCompanyFunding: (domain) => {
    return api.get(`/clay/company-funding/${domain}`);
  },
  
  // Get company profile
  getCompanyProfile: (domain) => {
    return api.get(`/clay/company-profile/${domain}`);
  },
  
  // Sync company data to HubSpot
  syncToHubspot: (domain) => {
    return api.post(`/clay/sync-to-hubspot/${domain}`);
  },
  
  // Create HubSpot properties
  createHubspotProperties: () => {
    return api.post('/clay/create-hubspot-properties');
  }
};

// Scheduler API endpoints
export const schedulerApi = {
  // Get scheduler status
  getStatus: () => {
    return api.get('/scheduler/status');
  },
  
  // Start the scheduler
  start: () => {
    return api.post('/scheduler/start');
  },
  
  // Stop the scheduler
  stop: () => {
    return api.post('/scheduler/stop');
  },
  
  // Add a task to the scheduler
  addTask: (taskData) => {
    return api.post('/scheduler/add-task', taskData);
  },
  
  // Remove a task from the scheduler
  removeTask: (taskId) => {
    return api.delete(`/scheduler/remove-task/${taskId}`);
  }
};

// HubSpot API endpoints
export const hubspotApi = {
  // Get companies from HubSpot
  getCompanies: (limit = 10, offset = 0) => {
    return api.get(`/hubspot/companies?limit=${limit}&offset=${offset}`);
  },
  
  // Get a specific company from HubSpot
  getCompany: (companyId) => {
    return api.get(`/hubspot/companies/${companyId}`);
  },
  
  // Search for companies in HubSpot
  searchCompanies: (query) => {
    return api.get(`/hubspot/companies/search?query=${query}`);
  }
};

export default api;
