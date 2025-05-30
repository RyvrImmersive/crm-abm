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
  Tab,
  Chip,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Pagination,
  Tooltip,
  IconButton,
  InputAdornment,
  FormGroup,
  FormControlLabel,
  Checkbox,
  Slider,
  Divider
} from '@mui/material';
import { hubspotApi, clayApi } from '../services/api';
import SearchIcon from '@mui/icons-material/Search';
import FilterListIcon from '@mui/icons-material/FilterList';
import SortIcon from '@mui/icons-material/Sort';
import RefreshIcon from '@mui/icons-material/Refresh';
import InfoIcon from '@mui/icons-material/Info';

const Companies = () => {
  // Main state
  const [companies, setCompanies] = useState([]);
  const [filteredCompanies, setFilteredCompanies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCompany, setSelectedCompany] = useState(null);
  const [companyData, setCompanyData] = useState({
    news: [],
    jobs: [],
    funding: [],
    profile: {}
  });
  
  // UI state
  const [dialogOpen, setDialogOpen] = useState(false);
  const [tabValue, setTabValue] = useState(0);
  const [refreshing, setRefreshing] = useState(false);
  const [filtersOpen, setFiltersOpen] = useState(false);
  
  // Pagination state
  const [page, setPage] = useState(1);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  
  // Filter state
  const [filters, setFilters] = useState({
    industry: '',
    size: '',
    scoreRange: [0, 100],
    hasScore: false,
    hasRecentUpdate: false,
    relationshipStatus: ''
  });
  
  // Sort state
  const [sortConfig, setSortConfig] = useState({
    key: 'name',
    direction: 'asc'
  });

  // Initialize and fetch companies
  useEffect(() => {
    const initialize = async () => {
      try {
        setLoading(true);
        // Create relationship status property in HubSpot if it doesn't exist
        // We'll do this in the background and not block the UI
        createRelationshipStatusProperty().catch(err => {
          console.warn('Could not create relationship status property:', err);
        });
        
        // Get all companies for initial load
        const response = await hubspotApi.getCompanies(100, 0);
        console.log('HubSpot API response:', response);
        
        // Handle different response formats
        let companiesData = [];
        if (response.data && response.data.results) {
          companiesData = response.data.results;
        } else if (Array.isArray(response.data)) {
          companiesData = response.data;
        } else if (response.data) {
          // Try to handle other formats
          console.log('Trying to parse response data:', response.data);
          if (typeof response.data === 'object') {
            // If it's an object but not what we expect, see if it has any array properties
            const possibleArrays = Object.values(response.data).filter(val => Array.isArray(val));
            if (possibleArrays.length > 0) {
              companiesData = possibleArrays[0]; // Use the first array found
              console.log('Found array in response:', companiesData);
            }
          }
        }
        
        console.log('Companies data extracted:', companiesData);
        
        if (companiesData.length === 0) {
          console.warn('No companies found in the response');
          // For testing, create some dummy data
          companiesData = [
            { id: '1', properties: { name: 'Example Corp', domain: 'example.com', industry: 'Technology' } },
            { id: '2', properties: { name: 'Test Inc', domain: 'test.com', industry: 'Finance' } }
          ];
        }
        
        // Enhance companies with score data and relationship status if available
        const enhancedCompanies = companiesData.map(company => ({
          ...company,
          score: {
            value: company.properties?.clay_score || null,
            lastUpdated: company.properties?.last_clay_update || null
          },
          relationshipStatus: company.properties?.relationship_status || null
        }));
        
        console.log('Enhanced companies:', enhancedCompanies);
        setCompanies(enhancedCompanies);
        setFilteredCompanies(enhancedCompanies); // Explicitly set filtered companies
        
        // Save companies to localStorage for persistence across page navigations
        localStorage.setItem('hubspot_companies', JSON.stringify(enhancedCompanies));
      } catch (error) {
        console.error('Error initializing:', error);
        // Try to load from localStorage if API fails
        const savedCompanies = localStorage.getItem('hubspot_companies');
        if (savedCompanies) {
          try {
            const parsedCompanies = JSON.parse(savedCompanies);
            setCompanies(parsedCompanies);
            setFilteredCompanies(parsedCompanies);
            console.log('Loaded companies from localStorage:', parsedCompanies);
          } catch (e) {
            console.error('Error parsing saved companies:', e);
          }
        }
      } finally {
        setLoading(false);
      }
    };

    initialize();
  }, []);

  // Apply filters and sorting
  useEffect(() => {
    // Always set filtered companies even if there are no companies
    // This ensures we don't lose the reference to filtered companies
    if (companies.length === 0) {
      setFilteredCompanies([]);
      return;
    }
    
    let result = [...companies];
    
    // Apply search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      result = result.filter(company => {
        return (
          (company.properties?.name || '').toLowerCase().includes(query) ||
          (company.properties?.domain || '').toLowerCase().includes(query) ||
          (company.properties?.industry || '').toLowerCase().includes(query)
        );
      });
    }
    
    // Apply industry filter
    if (filters.industry) {
      result = result.filter(company => 
        company.properties?.industry === filters.industry
      );
    }
    
    // Apply relationship status filter
    if (filters.relationshipStatus) {
      result = result.filter(company => 
        company.relationshipStatus === filters.relationshipStatus
      );
    }
    
    // Apply size filter
    if (filters.size) {
      result = result.filter(company => {
        const size = Number(company.properties?.numberofemployees || 0);
        switch(filters.size) {
          case 'small': return size > 0 && size < 50;
          case 'medium': return size >= 50 && size < 200;
          case 'large': return size >= 200;
          default: return true;
        }
      });
    }
    
    // Apply score filters
    if (filters.hasScore) {
      result = result.filter(company => company.score.value !== null);
    }
    
    if (filters.scoreRange[0] > 0 || filters.scoreRange[1] < 100) {
      result = result.filter(company => {
        const score = Number(company.score.value || 0);
        return score >= filters.scoreRange[0] && score <= filters.scoreRange[1];
      });
    }
    
    // Apply recent update filter
    if (filters.hasRecentUpdate) {
      const thirtyDaysAgo = new Date();
      thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
      
      result = result.filter(company => {
        if (!company.score.lastUpdated) return false;
        const updateDate = new Date(company.score.lastUpdated);
        return updateDate > thirtyDaysAgo;
      });
    }
    
    // Apply sorting
    result.sort((a, b) => {
      let aValue, bValue;
      
      switch(sortConfig.key) {
        case 'name':
          aValue = a.properties?.name || '';
          bValue = b.properties?.name || '';
          break;
        case 'domain':
          aValue = a.properties?.domain || '';
          bValue = b.properties?.domain || '';
          break;
        case 'industry':
          aValue = a.properties?.industry || '';
          bValue = b.properties?.industry || '';
          break;
        case 'size':
          aValue = Number(a.properties?.numberofemployees || 0);
          bValue = Number(b.properties?.numberofemployees || 0);
          break;
        case 'score':
          aValue = Number(a.score.value || 0);
          bValue = Number(b.score.value || 0);
          break;
        case 'lastUpdated':
          aValue = a.score.lastUpdated ? new Date(a.score.lastUpdated) : new Date(0);
          bValue = b.score.lastUpdated ? new Date(b.score.lastUpdated) : new Date(0);
          break;
        default:
          aValue = a.properties?.name || '';
          bValue = b.properties?.name || '';
      }
      
      if (sortConfig.direction === 'asc') {
        return aValue > bValue ? 1 : -1;
      } else {
        return aValue < bValue ? 1 : -1;
      }
    });
    
    setFilteredCompanies(result);
  }, [companies, searchQuery, filters, sortConfig]);

  // Define relationship status options
  const relationshipStatusOptions = [
    { value: "Current Customer", label: "Current Customer", color: "success" },
    { value: "Sales Prospect", label: "Sales Prospect", color: "primary" },
    { value: "Marketing Prospect", label: "Marketing Prospect", color: "info" },
    { value: "Do Not Call", label: "Do Not Call", color: "error" },
    { value: "Current Opportunity", label: "Current Opportunity", color: "warning" },
    { value: "Competition", label: "Competition", color: "secondary" },
    { value: "Influencer", label: "Influencer", color: "default" },
  ];

  // Handle search input change
  const handleSearchChange = (e) => {
    setSearchQuery(e.target.value);
  };
  
  // Handle search submit
  const handleSearchSubmit = (e) => {
    e.preventDefault();
    // The filtering is handled by the useEffect
  };
  
  // Handle filter changes
  const handleFilterChange = (filterName, value) => {
    setFilters(prev => ({
      ...prev,
      [filterName]: value
    }));
  };
  
  // Handle sort changes
  const handleSortChange = (key) => {
    setSortConfig(prev => ({
      key,
      direction: prev.key === key && prev.direction === 'asc' ? 'desc' : 'asc'
    }));
  };
  
  // Handle pagination change
  const handlePageChange = (event, newPage) => {
    setPage(newPage);
  };
  
  // Handle rows per page change
  const handleRowsPerPageChange = (event) => {
    setRowsPerPage(Number(event.target.value || 10));
    setPage(1);
  };
  
  // Get unique industries for filter dropdown
  const getUniqueIndustries = () => {
    const industries = companies
      .map(company => company.properties?.industry)
      .filter(industry => industry);
    return [...new Set(industries)];
  };
  
  // Get paginated data
  const getPaginatedData = () => {
    const startIndex = (page - 1) * rowsPerPage;
    return filteredCompanies.slice(startIndex, startIndex + rowsPerPage);
  };
  
  // Reset filters
  const resetFilters = () => {
    setFilters({
      industry: '',
      size: '',
      scoreRange: [0, 100],
      hasScore: false,
      hasRecentUpdate: false,
      relationshipStatus: ''
    });
    setSearchQuery('');
    setSortConfig({
      key: 'name',
      direction: 'asc'
    });
  };
  
  // Refresh companies data
  const refreshCompanies = async () => {
    try {
      setLoading(true);
      const response = await hubspotApi.getCompanies(100, 0);
      
      let companiesData = [];
      if (response.data && response.data.results) {
        companiesData = response.data.results;
      } else if (Array.isArray(response.data)) {
        companiesData = response.data;
      }
      
      const enhancedCompanies = companiesData.map(company => ({
        ...company,
        score: {
          value: company.properties?.clay_score || null,
          lastUpdated: company.properties?.last_clay_update || null
        },
        relationshipStatus: company.properties?.relationship_status || null
      }));
      
      setCompanies(enhancedCompanies);
    } catch (error) {
      console.error('Error refreshing companies:', error);
    } finally {
      setLoading(false);
    }
  };
  
  // Check for relationship status on mount and create if needed
  const createRelationshipStatusProperty = async () => {
    try {
      const response = await hubspotApi.createRelationshipStatusProperty();
      console.log('Relationship status property check:', response.data);
      return response.data;
    } catch (error) {
      console.error('Error checking/creating relationship status property:', error);
      throw error;
    }
  };
  
  // Helper function to apply all filters to a company
  const applyFilters = (company) => {
    // If no filters are active, return true
    if (!filters.industry && !filters.size && !filters.hasScore && 
        !filters.hasRecentUpdate && !filters.relationshipStatus && 
        filters.scoreRange[0] === 0 && filters.scoreRange[1] === 100) {
      return true;
    }
    
    // Apply industry filter
    if (filters.industry && company.properties?.industry !== filters.industry) {
      return false;
    }
    
    // Apply size filter
    if (filters.size) {
      const employeeCount = parseInt(company.properties?.numberofemployees) || 0;
      if (filters.size === 'small' && employeeCount > 50) return false;
      if (filters.size === 'medium' && (employeeCount <= 50 || employeeCount > 500)) return false;
      if (filters.size === 'large' && employeeCount <= 500) return false;
    }
    
    // Apply score filter
    if (filters.hasScore && !company.score?.value) {
      return false;
    }
    
    // Apply recent update filter
    if (filters.hasRecentUpdate && !company.score?.lastUpdated) {
      return false;
    }
    
    // Apply relationship status filter
    if (filters.relationshipStatus && company.relationshipStatus !== filters.relationshipStatus) {
      return false;
    }
    
    // Apply score range filter
    if (company.score?.value) {
      const score = parseFloat(company.score.value) * 100;
      if (score < filters.scoreRange[0] || score > filters.scoreRange[1]) {
        return false;
      }
    }
    
    return true;
  };
  
  // Load companies from localStorage when component mounts
  useEffect(() => {
    const savedCompanies = localStorage.getItem('hubspot_companies');
    if (savedCompanies && companies.length === 0 && !loading) {
      try {
        const parsedCompanies = JSON.parse(savedCompanies);
        if (parsedCompanies && parsedCompanies.length > 0) {
          setCompanies(parsedCompanies);
          setFilteredCompanies(parsedCompanies);
          console.log('Loaded companies from localStorage on mount:', parsedCompanies);
        }
      } catch (e) {
        console.error('Error parsing saved companies on mount:', e);
      }
    }
  }, []);

  // Update relationship status for a company
  const updateRelationshipStatus = async (companyId, status) => {
    try {
      setLoading(true);
      await hubspotApi.updateRelationshipStatus(companyId, status);
      
      // Update the local state
      const updatedCompanies = companies.map(company => {
        if (company.id === companyId) {
          return {
            ...company,
            relationshipStatus: status,
            properties: {
              ...company.properties,
              relationship_status: status
            }
          };
        }
        return company;
      });
      
      setCompanies(updatedCompanies);
      setFilteredCompanies(updatedCompanies.filter(company => applyFilters(company)));
      
      // Update localStorage to persist changes
      localStorage.setItem('hubspot_companies', JSON.stringify(updatedCompanies));
      
      // Show success message
      alert(`Relationship status updated to ${status}`);
    } catch (error) {
      console.error('Error updating relationship status:', error);
      alert('Error updating relationship status');
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
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4">
          Companies
        </Typography>
        <Box>
          <Tooltip title="Refresh Companies Data">
            <IconButton onClick={refreshCompanies} disabled={loading}>
              <RefreshIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>
      
      {/* Search and Filter Bar */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Grid container spacing={2}>
          {/* Search */}
          <Grid item xs={12} md={6}>
            <form onSubmit={handleSearchSubmit}>
              <TextField
                fullWidth
                label="Search Companies"
                variant="outlined"
                value={searchQuery}
                onChange={handleSearchChange}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchIcon />
                    </InputAdornment>
                  ),
                }}
              />
            </form>
          </Grid>
          
          {/* Filter Toggle */}
          <Grid item xs={12} md={6}>
            <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 1 }}>
              <Button 
                variant={filtersOpen ? "contained" : "outlined"}
                startIcon={<FilterListIcon />}
                onClick={() => setFiltersOpen(!filtersOpen)}
              >
                Filters
              </Button>
              <Button 
                variant="outlined"
                startIcon={<SortIcon />}
                onClick={() => handleSortChange('name')}
              >
                Sort
              </Button>
              {(filters.industry || filters.size || filters.hasScore || filters.hasRecentUpdate || 
                filters.scoreRange[0] > 0 || filters.scoreRange[1] < 100) && (
                <Button 
                  variant="outlined" 
                  color="error"
                  onClick={resetFilters}
                >
                  Clear Filters
                </Button>
              )}
            </Box>
          </Grid>
          
          {/* Expanded Filters */}
          {filtersOpen && (
            <Grid item xs={12}>
              <Paper sx={{ p: 2, bgcolor: 'background.default' }}>
                <Grid container spacing={2}>
                  {/* Industry Filter */}
                  <Grid item xs={12} md={3}>
                    <FormControl fullWidth>
                      <InputLabel>Industry</InputLabel>
                      <Select
                        value={filters.industry}
                        onChange={(e) => handleFilterChange('industry', e.target.value)}
                        label="Industry"
                      >
                        <MenuItem value="">All Industries</MenuItem>
                        {getUniqueIndustries().map(industry => (
                          <MenuItem key={industry} value={industry}>{industry}</MenuItem>
                        ))}
                      </Select>
                    </FormControl>
                  </Grid>
                  
                  {/* Relationship Status Filter */}
                  <Grid item xs={12} md={3}>
                    <FormControl fullWidth>
                      <InputLabel>Relationship Status</InputLabel>
                      <Select
                        value={filters.relationshipStatus}
                        onChange={(e) => handleFilterChange('relationshipStatus', e.target.value)}
                        label="Relationship Status"
                      >
                        <MenuItem value="">All Statuses</MenuItem>
                        {relationshipStatusOptions.map(option => (
                          <MenuItem key={option.value} value={option.value}>
                            <Chip 
                              label={option.label} 
                              size="small" 
                              color={option.color}
                              sx={{ mr: 1 }}
                            />
                            {option.label}
                          </MenuItem>
                        ))}
                      </Select>
                    </FormControl>
                  </Grid>
                  
                  {/* Size Filter */}
                  <Grid item xs={12} md={4}>
                    <FormControl fullWidth>
                      <InputLabel>Company Size</InputLabel>
                      <Select
                        value={filters.size}
                        onChange={(e) => handleFilterChange('size', e.target.value)}
                        label="Company Size"
                      >
                        <MenuItem value="">All Sizes</MenuItem>
                        <MenuItem value="small">Small (&lt;50)</MenuItem>
                        <MenuItem value="medium">Medium (50-199)</MenuItem>
                        <MenuItem value="large">Large (200+)</MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>
                  
                  {/* Score Range Filter */}
                  <Grid item xs={12} md={4}>
                    <Typography gutterBottom>Score Range</Typography>
                    <Slider
                      value={filters.scoreRange}
                      onChange={(e, newValue) => handleFilterChange('scoreRange', newValue)}
                      valueLabelDisplay="auto"
                      min={0}
                      max={100}
                      disabled={!filters.hasScore}
                    />
                  </Grid>
                  
                  {/* Checkbox Filters */}
                  <Grid item xs={12}>
                    <FormGroup row>
                      <FormControlLabel
                        control={
                          <Checkbox 
                            checked={filters.hasScore} 
                            onChange={(e) => handleFilterChange('hasScore', e.target.checked)}
                          />
                        }
                        label="Has Score"
                      />
                      <FormControlLabel
                        control={
                          <Checkbox 
                            checked={filters.hasRecentUpdate} 
                            onChange={(e) => handleFilterChange('hasRecentUpdate', e.target.checked)}
                          />
                        }
                        label="Updated in Last 30 Days"
                      />
                    </FormGroup>
                  </Grid>
                </Grid>
              </Paper>
            </Grid>
          )}
        </Grid>
      </Paper>
      
      {/* Results Summary */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="body2">
          Showing {filteredCompanies.length} of {companies.length} companies
        </Typography>
        <FormControl variant="outlined" size="small" sx={{ minWidth: 120 }}>
          <InputLabel>Rows</InputLabel>
          <Select
            value={rowsPerPage}
            onChange={handleRowsPerPageChange}
            label="Rows"
          >
            <MenuItem value={5}>5</MenuItem>
            <MenuItem value={10}>10</MenuItem>
            <MenuItem value={25}>25</MenuItem>
            <MenuItem value={50}>50</MenuItem>
          </Select>
        </FormControl>
      </Box>
      
      {loading ? (
        <Box display="flex" justifyContent="center" my={4}>
          <CircularProgress />
        </Box>
      ) : (
        <>
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell 
                    onClick={() => handleSortChange('name')}
                    sx={{ cursor: 'pointer' }}
                  >
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      Name
                      {sortConfig.key === 'name' && (
                        <SortIcon fontSize="small" sx={{ 
                          ml: 0.5,
                          transform: sortConfig.direction === 'desc' ? 'rotate(180deg)' : 'none'
                        }} />
                      )}
                    </Box>
                  </TableCell>
                  <TableCell 
                    onClick={() => handleSortChange('domain')}
                    sx={{ cursor: 'pointer' }}
                  >
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      Domain
                      {sortConfig.key === 'domain' && (
                        <SortIcon fontSize="small" sx={{ 
                          ml: 0.5,
                          transform: sortConfig.direction === 'desc' ? 'rotate(180deg)' : 'none'
                        }} />
                      )}
                    </Box>
                  </TableCell>
                  <TableCell 
                    onClick={() => handleSortChange('industry')}
                    sx={{ cursor: 'pointer' }}
                  >
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      Industry
                      {sortConfig.key === 'industry' && (
                        <SortIcon fontSize="small" sx={{ 
                          ml: 0.5,
                          transform: sortConfig.direction === 'desc' ? 'rotate(180deg)' : 'none'
                        }} />
                      )}
                    </Box>
                  </TableCell>
                  <TableCell 
                    onClick={() => handleSortChange('score')}
                    sx={{ cursor: 'pointer' }}
                  >
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      Score
                      {sortConfig.key === 'score' && (
                        <SortIcon fontSize="small" sx={{ 
                          ml: 0.5,
                          transform: sortConfig.direction === 'desc' ? 'rotate(180deg)' : 'none'
                        }} />
                      )}
                    </Box>
                  </TableCell>
                  <TableCell 
                    onClick={() => handleSortChange('lastUpdated')}
                    sx={{ cursor: 'pointer' }}
                  >
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      Last Updated
                      {sortConfig.key === 'lastUpdated' && (
                        <SortIcon fontSize="small" sx={{ 
                          ml: 0.5,
                          transform: sortConfig.direction === 'desc' ? 'rotate(180deg)' : 'none'
                        }} />
                      )}
                    </Box>
                  </TableCell>
                  <TableCell>Relationship Status</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {getPaginatedData().length > 0 ? (
                  getPaginatedData().map((company) => (
                    <TableRow key={company.id}>
                      <TableCell>{company.properties?.name || 'N/A'}</TableCell>
                      <TableCell>{company.properties?.domain || 'N/A'}</TableCell>
                      <TableCell>
                        {company.properties?.industry ? (
                          <Chip 
                            label={company.properties.industry} 
                            size="small" 
                            variant="outlined"
                          />
                        ) : 'N/A'}
                      </TableCell>
                      <TableCell>
                        {company.score.value ? (
                          <Chip 
                            label={company.score.value} 
                            color={Number(company.score.value || 0) > 70 ? "success" : 
                                  Number(company.score.value || 0) > 40 ? "warning" : "error"}
                            sx={{ fontWeight: 'bold' }}
                          />
                        ) : 'N/A'}
                      </TableCell>
                      <TableCell>
                        {company.score.lastUpdated ? 
                          new Date(company.score.lastUpdated).toLocaleDateString() : 'Never'}
                      </TableCell>
                      <TableCell>
                        <FormControl size="small" fullWidth>
                          <Select
                            value={company.relationshipStatus || ''}
                            onChange={(e) => updateRelationshipStatus(company.id, e.target.value)}
                            displayEmpty
                            sx={{ minWidth: 180 }}
                            renderValue={(selected) => {
                              if (!selected) {
                                return <em>Set Status</em>;
                              }
                              const option = relationshipStatusOptions.find(opt => opt.value === selected);
                              return (
                                <Chip 
                                  label={selected} 
                                  size="small" 
                                  color={option?.color || 'default'}
                                />
                              );
                            }}
                          >
                            <MenuItem value="">
                              <em>None</em>
                            </MenuItem>
                            {relationshipStatusOptions.map((option) => (
                              <MenuItem key={option.value} value={option.value}>
                                <Chip 
                                  label={option.label} 
                                  size="small" 
                                  color={option.color}
                                  sx={{ mr: 1 }}
                                />
                                {option.label}
                              </MenuItem>
                            ))}
                          </Select>
                        </FormControl>
                      </TableCell>
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
                    <TableCell colSpan={6} align="center">
                      No companies found
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </TableContainer>
          
          {/* Pagination */}
          <Box sx={{ display: 'flex', justifyContent: 'center', mt: 3 }}>
            <Pagination 
              count={Math.ceil(filteredCompanies.length / rowsPerPage)} 
              page={page} 
              onChange={handlePageChange} 
              color="primary" 
              showFirstButton 
              showLastButton
            />
          </Box>
        </>
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
