import axios from 'axios';

// Create an axios instance with default config
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000/api',
  headers: {
    'Content-Type': 'application/json',
  },
  // Add better error handling
  validateStatus: function (status) {
    return status >= 200 && status < 500; // Handle all non-500 responses
  },
});

// Add response interceptor for debugging
api.interceptors.response.use(
  response => {
    console.log(`API Response [${response.config.method}] ${response.config.url}:`, response.status);
    return response;
  },
  error => {
    console.error('API Error:', error.response || error.message || error);
    return Promise.reject(error);
  }
);

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
  // Get companies
  getCompanies: (limit = 10, offset = 0) => {
    console.log(`Fetching companies with limit=${limit}, offset=${offset}`);
    return api.get(`/hubspot/companies?limit=${limit}&offset=${offset}`)
      .then(response => {
        console.log('HubSpot companies API response:', response);
        return response;
      })
      .catch(error => {
        console.error('Error fetching HubSpot companies:', error);
        throw error;
      });
  },
  
  // Get a specific company
  getCompany: (id) => api.get(`/hubspot/companies/${id}`),
  
  // Search companies
  searchCompanies: (query) => api.get(`/hubspot/companies/search?query=${query}`),
  
  // Get company properties
  getProperties: () => api.get('/hubspot/properties'),
  
  // Create relationship status property
  createRelationshipStatusProperty: () => api.post('/hubspot/properties/create-relationship-status'),
  
  // Update relationship status for a company
  updateRelationshipStatus: (companyId, status) => api.post('/hubspot/companies/update-relationship-status', {
    company_id: companyId,
    status: status
  }),
};

// Scoring API endpoints
export const scoringApi = {
  // Get current weights
  getWeights: () => api.get('/scoring/weights'),
  
  // Update weights
  updateWeights: (weights) => api.post('/scoring/weights', { weights }),
  
  // Reset weights to default
  resetWeights: () => api.post('/scoring/weights/reset'),
  
  // Score an entity
  scoreEntity: (entity, weights = null) => api.post('/scoring/score', { 
    entity,
    weights
  }),
};

export default api;
