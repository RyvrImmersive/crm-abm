import axios from 'axios';

// API base URL - will be different for development vs production
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30 seconds timeout
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for logging
api.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    console.log(`API Response: ${response.status} ${response.config.url}`);
    return response;
  },
  (error) => {
    console.error('API Response Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// Company Research API functions
export const companyResearchApi = {
  // Health check
  healthCheck: async () => {
    try {
      const response = await api.get('/health');
      return response.data;
    } catch (error) {
      throw new Error(`Health check failed: ${error.message}`);
    }
  },

  // Research a company
  researchCompany: async (companyData) => {
    try {
      // Use longer timeout for research calls (3 minutes)
      const response = await api.post('/research', companyData, {
        timeout: 180000 // 3 minutes for new company research
      });
      console.log('API Response:', response.data); // Debug logging
      return response.data;
    } catch (error) {
      console.error('API Error:', error); // Debug logging
      if (error.code === 'ECONNABORTED') {
        throw new Error('Research timeout: This company may not be in our database. Please try a different company or check back later.');
      }
      throw new Error(`Company research failed: ${error.response?.data?.detail || error.message}`);
    }
  },

  // Find lookalike companies
  findLookalikeCompanies: async (companyData) => {
    try {
      const response = await api.post('/lookalike', { company_data: companyData });
      return response.data;
    } catch (error) {
      throw new Error(`Lookalike search failed: ${error.response?.data?.detail || error.message}`);
    }
  },

  // Get platform stats
  getStats: async () => {
    try {
      const response = await api.get('/stats');
      return response.data;
    } catch (error) {
      throw new Error(`Failed to get stats: ${error.message}`);
    }
  },

  // Analyze sentiment
  analyzeSentiment: async (sources) => {
    try {
      const response = await api.post('/sentiment', sources);
      return response.data;
    } catch (error) {
      throw new Error(`Sentiment analysis failed: ${error.message}`);
    }
  }
};

export default companyResearchApi;
