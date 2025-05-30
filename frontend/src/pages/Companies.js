import React, { useState, useEffect } from 'react';
import { 
  Container, 
  Typography, 
  Grid, 
  Paper, 
  Box, 
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Button,
  TextField,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Tabs,
  Tab
} from '@mui/material';
import { hubspotApi, clayApi } from '../services/api';

const Companies = () => {
  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCompany, setSelectedCompany] = useState(null);
  const [companyData, setCompanyData] = useState({
    news: [],
    jobs: [],
    funding: [],
    profile: {}
  });
  const [dialogOpen, setDialogOpen] = useState(false);
  const [tabValue, setTabValue] = useState(0);
  const [refreshing, setRefreshing] = useState(false);

  // Fetch companies from HubSpot
  useEffect(() => {
    const fetchCompanies = async () => {
      try {
        setLoading(true);
        const response = await hubspotApi.getCompanies(50, 0);
        console.log('HubSpot API response:', response.data);
        
        // Handle different response formats
        if (response.data && response.data.results) {
          setCompanies(response.data.results);
        } else if (Array.isArray(response.data)) {
          setCompanies(response.data);
        } else {
          console.error('Unexpected response format:', response.data);
          setCompanies([]);
        }
      } catch (error) {
        console.error('Error fetching companies:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchCompanies();
  }, []);

  // Handle search
  const handleSearch = async () => {
    if (!searchQuery) return;
    
    try {
      setLoading(true);
      const response = await hubspotApi.searchCompanies(searchQuery);
      console.log('Search response:', response.data);
      
      // Handle different response formats
      if (response.data && response.data.results) {
        setCompanies(response.data.results);
      } else if (Array.isArray(response.data)) {
        setCompanies(response.data);
      } else {
        console.error('Unexpected search response format:', response.data);
        setCompanies([]);
      }
    } catch (error) {
      console.error('Error searching companies:', error);
    } finally {
      setLoading(false);
    }
  };

  // Handle company selection
  const handleCompanyClick = async (company) => {
    setSelectedCompany(company);
    setDialogOpen(true);
    await fetchCompanyData(company.properties.domain);
  };

  // Fetch company data from Clay
  const fetchCompanyData = async (domain) => {
    try {
      setRefreshing(true);
      
      // Fetch news
      const newsResponse = await clayApi.getCompanyNews(domain);
      
      // Fetch jobs
      const jobsResponse = await clayApi.getCompanyJobs(domain);
      
      // Fetch funding
      const fundingResponse = await clayApi.getCompanyFunding(domain);
      
      // Fetch profile
      const profileResponse = await clayApi.getCompanyProfile(domain);
      
      setCompanyData({
        news: newsResponse.data.news || [],
        jobs: jobsResponse.data.jobs || [],
        funding: fundingResponse.data.funding || [],
        profile: profileResponse.data.profile || {}
      });
    } catch (error) {
      console.error('Error fetching company data:', error);
    } finally {
      setRefreshing(false);
    }
  };

  // Handle sync to HubSpot
  const handleSyncToHubspot = async (domain) => {
    try {
      setRefreshing(true);
      await clayApi.syncToHubspot(domain);
      alert(`Syncing data for ${domain} to HubSpot initiated!`);
    } catch (error) {
      console.error('Error syncing to HubSpot:', error);
      alert('Error syncing to HubSpot. See console for details.');
    } finally {
      setRefreshing(false);
    }
  };

  // Handle tab change
  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom>
        Companies
      </Typography>
      
      {/* Search Bar */}
      <Box sx={{ mb: 4, display: 'flex', alignItems: 'center' }}>
        <TextField
          label="Search Companies"
          variant="outlined"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          sx={{ mr: 2, flexGrow: 1 }}
        />
        <Button 
          variant="contained" 
          onClick={handleSearch}
          disabled={loading || !searchQuery}
        >
          Search
        </Button>
      </Box>
      
      {loading ? (
        <Box display="flex" justifyContent="center" my={4}>
          <CircularProgress />
        </Box>
      ) : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Name</TableCell>
                <TableCell>Domain</TableCell>
                <TableCell>Industry</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {companies.length > 0 ? (
                companies.map((company) => (
                  <TableRow key={company.id}>
                    <TableCell>{company.properties?.name || 'N/A'}</TableCell>
                    <TableCell>{company.properties?.domain || 'N/A'}</TableCell>
                    <TableCell>{company.properties?.industry || 'N/A'}</TableCell>
                    <TableCell>
                      <Button 
                        variant="outlined" 
                        size="small"
                        onClick={() => handleCompanyClick(company)}
                        sx={{ mr: 1 }}
                        disabled={!company.properties?.domain}
                      >
                        View
                      </Button>
                      <Button 
                        variant="contained" 
                        size="small"
                        onClick={() => handleSyncToHubspot(company.properties?.domain)}
                        disabled={!company.properties?.domain}
                      >
                        Sync
                      </Button>
                    </TableCell>
                  </TableRow>
                ))
              ) : (
                <TableRow>
                  <TableCell colSpan={4} align="center">
                    No companies found
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>
      )}
      
      {/* Company Detail Dialog */}
      {selectedCompany && (
        <Dialog 
          open={dialogOpen} 
          onClose={() => setDialogOpen(false)}
          fullWidth
          maxWidth="md"
        >
          <DialogTitle>
            {selectedCompany.properties.name}
            {refreshing && (
              <CircularProgress size={20} sx={{ ml: 2 }} />
            )}
          </DialogTitle>
          <DialogContent>
            <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}>
              <Tabs value={tabValue} onChange={handleTabChange}>
                <Tab label="Overview" />
                <Tab label="News" />
                <Tab label="Jobs" />
                <Tab label="Funding" />
              </Tabs>
            </Box>
            
            {/* Overview Tab */}
            {tabValue === 0 && (
              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle1">Domain:</Typography>
                  <Typography variant="body1">{selectedCompany.properties.domain}</Typography>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle1">Industry:</Typography>
                  <Typography variant="body1">{selectedCompany.properties.industry || 'N/A'}</Typography>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle1">Employees:</Typography>
                  <Typography variant="body1">{selectedCompany.properties.numberofemployees || 'N/A'}</Typography>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle1">LinkedIn:</Typography>
                  <Typography variant="body1">
                    {selectedCompany.properties.linkedin_company_page ? (
                      <a href={selectedCompany.properties.linkedin_company_page} target="_blank" rel="noopener noreferrer">
                        {selectedCompany.properties.linkedin_company_page}
                      </a>
                    ) : 'N/A'}
                  </Typography>
                </Grid>
                <Grid item xs={12}>
                  <Typography variant="subtitle1">Description:</Typography>
                  <Typography variant="body1">{selectedCompany.properties.description || 'N/A'}</Typography>
                </Grid>
              </Grid>
            )}
            
            {/* News Tab */}
            {tabValue === 1 && (
              <>
                {companyData.news.length > 0 ? (
                  companyData.news.map((newsItem, index) => (
                    <Paper key={index} sx={{ p: 2, mb: 2 }}>
                      <Typography variant="h6">
                        <a href={newsItem.url} target="_blank" rel="noopener noreferrer">
                          {newsItem.title}
                        </a>
                      </Typography>
                      <Typography variant="caption">
                        {new Date(newsItem.published_date).toLocaleDateString()}
                      </Typography>
                      <Typography variant="body2" sx={{ mt: 1 }}>
                        {newsItem.description}
                      </Typography>
                    </Paper>
                  ))
                ) : (
                  <Typography>No news found for this company</Typography>
                )}
              </>
            )}
            
            {/* Jobs Tab */}
            {tabValue === 2 && (
              <>
                {companyData.jobs.length > 0 ? (
                  companyData.jobs.map((job, index) => (
                    <Paper key={index} sx={{ p: 2, mb: 2 }}>
                      <Typography variant="h6">
                        <a href={job.url} target="_blank" rel="noopener noreferrer">
                          {job.title}
                        </a>
                      </Typography>
                      <Typography variant="caption">
                        {job.location || 'Remote'} • {job.type || 'Full-time'}
                      </Typography>
                      <Typography variant="body2" sx={{ mt: 1 }}>
                        {job.description ? job.description.substring(0, 200) + '...' : 'No description available'}
                      </Typography>
                    </Paper>
                  ))
                ) : (
                  <Typography>No job postings found for this company</Typography>
                )}
              </>
            )}
            
            {/* Funding Tab */}
            {tabValue === 3 && (
              <>
                {companyData.funding.length > 0 ? (
                  companyData.funding.map((round, index) => (
                    <Paper key={index} sx={{ p: 2, mb: 2 }}>
                      <Typography variant="h6">
                        {round.round_type || 'Funding Round'}: ${(round.amount / 1000000).toFixed(2)}M
                      </Typography>
                      <Typography variant="caption">
                        {new Date(round.date).toLocaleDateString()}
                      </Typography>
                      <Typography variant="body2" sx={{ mt: 1 }}>
                        Lead Investor: {round.lead_investor || 'Unknown'}
                      </Typography>
                    </Paper>
                  ))
                ) : (
                  <Typography>No funding information found for this company</Typography>
                )}
              </>
            )}
          </DialogContent>
          <DialogActions>
            <Button 
              onClick={() => fetchCompanyData(selectedCompany.properties.domain)}
              disabled={refreshing}
            >
              Refresh Data
            </Button>
            <Button 
              onClick={() => handleSyncToHubspot(selectedCompany.properties.domain)}
              disabled={refreshing}
              color="primary"
            >
              Sync to HubSpot
            </Button>
            <Button onClick={() => setDialogOpen(false)}>
              Close
            </Button>
          </DialogActions>
        </Dialog>
      )}
    </Container>
  );
};

export default Companies;
