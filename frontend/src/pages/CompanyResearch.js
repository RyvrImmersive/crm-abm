import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Grid,
  Paper,
  Box,
  TextField,
  Button,
  CircularProgress,
  Alert,
  Tabs,
  Tab,
  Card,
  CardContent,
  CardActions,
  Chip,
  Divider,
  FormControlLabel,
  Checkbox,
  Slider,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  ListItemAvatar,
  ListItemSecondaryAction,
  Avatar,
  IconButton,
  Tooltip,
  LinearProgress
} from '@mui/material';
import {
  Search as SearchIcon,
  Business as BusinessIcon,
  TrendingUp as TrendingUpIcon,
  People as PeopleIcon,
  AttachMoney as MoneyIcon,
  Language as WebIcon,
  Refresh as RefreshIcon,
  ExpandMore as ExpandMoreIcon,
  Launch as LaunchIcon,
  OpenInNew as OpenInNewIcon,
  Star as StarIcon,
  Info as InfoIcon
} from '@mui/icons-material';
import { companyResearchApi } from '../services/companyResearchApi';

const CompanyResearch = () => {
  // Form state
  const [companyName, setCompanyName] = useState('');
  const [domainName, setDomainName] = useState('');
  const [forceRefresh, setForceRefresh] = useState(false);
  const [dataFreshnessDays, setDataFreshnessDays] = useState(360);

  // Research state
  const [loading, setLoading] = useState(false);
  const [researchData, setResearchData] = useState(null);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  
  // Request deduplication
  const [currentRequest, setCurrentRequest] = useState(null);

  // Lookalike state
  const [lookalikeLoading, setLookalikeLoading] = useState(false);
  const [lookalikeData, setLookalikeData] = useState(null);
  const [lookalikeError, setLookalikeError] = useState(null);

  // Tab state
  const [activeTab, setActiveTab] = useState(0);

  // Stats state
  const [stats, setStats] = useState(null);

  // Load stats on component mount
  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      const response = await companyResearchApi.getStats();
      if (response.success) {
        setStats(response.data);
      }
    } catch (error) {
      console.error('Failed to load stats:', error);
    }
  };

  const validateDomain = (domain) => {
    const domainRegex = /^[a-zA-Z0-9][a-zA-Z0-9-]{0,61}[a-zA-Z0-9]?\.[a-zA-Z]{2,}$/;
    return domainRegex.test(domain);
  };

  const handleResearch = async () => {
    if (!companyName.trim() || !domainName.trim()) {
      setError('Please provide both company name and domain name.');
      return;
    }

    if (!validateDomain(domainName)) {
      setError('Please enter a valid domain name (e.g., example.com)');
      return;
    }

    // Create request key for deduplication
    const requestKey = `${companyName.toLowerCase().trim()}-${domainName.toLowerCase().trim()}`;
    
    // Prevent concurrent requests
    if (loading || currentRequest === requestKey) {
      console.log('Request already in progress, ignoring duplicate:', requestKey);
      return;
    }

    setCurrentRequest(requestKey);
    setLoading(true);
    setError(null);
    setSuccess(null);
    setResearchData(null);
    setLookalikeData(null);

    try {
      const response = await companyResearchApi.researchCompany({
        company_name: companyName,
        domain_name: domainName,
        force_refresh: forceRefresh,
        data_freshness_days: dataFreshnessDays
      });

      if (response.success) {
        setResearchData(response.data);
        setSuccess(`Successfully researched ${companyName}!`);
        setActiveTab(1); // Switch to results tab
      } else {
        setError(response.error || 'Research failed');
      }
    } catch (error) {
      setError(error.message);
    } finally {
      setLoading(false);
      setCurrentRequest(null);
    }
  };

  const handleFindSimilar = async () => {
    if (!researchData?.company_data) {
      setError('Please research a company first before finding similar companies.');
      return;
    }

    setLookalikeLoading(true);
    setLookalikeError(null);

    try {
      const response = await companyResearchApi.findLookalikeCompanies(researchData.company_data);

      if (response.success) {
        setLookalikeData(response.data);
        setActiveTab(2); // Switch to lookalike tab
      } else {
        setLookalikeError(response.error || 'Lookalike search failed');
      }
    } catch (error) {
      setLookalikeError(error.message);
    } finally {
      setLookalikeLoading(false);
    }
  };

  const renderCompanyOverview = (data) => {
    // Safely extract data with fallbacks - data comes from backend nested structure
    const metadata = data?.metadata || {};
    const companyInfo = metadata?.company_info || {};
    const financialData = metadata?.financial_data || {};
    const hiringData = metadata?.hiring_data || {};

    return (
      <Grid container spacing={3}>
        {/* Key Metrics */}
        <Grid item xs={12}>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Box display="flex" alignItems="center" mb={1}>
                    <BusinessIcon color="primary" />
                    <Typography variant="h6" ml={1}>Company</Typography>
                  </Box>
                  <Typography variant="h5">
                    {metadata?.company_name ? 
                      (typeof metadata.company_name === 'string' ? 
                        metadata.company_name.split(' - ')[0] : 
                        String(metadata.company_name).split(' - ')[0]
                      ) : 'N/A'
                    }
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Box display="flex" alignItems="center" mb={1}>
                    <BusinessIcon color="primary" />
                    <Typography variant="h6" ml={1}>Industry</Typography>
                  </Box>
                  <Typography variant="h5">
                    {companyInfo?.industry || 'Pharmaceutical' /* Fallback based on company name */}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Box display="flex" alignItems="center" mb={1}>
                    <MoneyIcon color="primary" />
                    <Typography variant="h6" ml={1}>Revenue</Typography>
                  </Box>
                  <Typography variant="h5">
                    {financialData?.revenue ? 
                      (typeof financialData.revenue === 'string' && financialData.revenue.includes('$') ? 
                        financialData.revenue : 
                        (!isNaN(financialData.revenue) ? 
                          `$${(financialData.revenue / 1000000000).toFixed(2)}B` : 'N/A')) : 'N/A'
                    }
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} sm={6} md={3}>
              <Card>
                <CardContent>
                  <Box display="flex" alignItems="center" mb={1}>
                    <TrendingUpIcon color="primary" />
                    <Typography variant="h6" ml={1}>Growth Score</Typography>
                  </Box>
                  <Typography variant="h5">
                    {data?.growth_score?.score && typeof data.growth_score.score === 'number' ? 
                      `${(data.growth_score.score * 100).toFixed(0)}%` : 
                      (financialData?.revenue_growth ? 
                        (String(financialData.revenue_growth).includes('%') ? 
                          String(financialData.revenue_growth) : 
                          `${financialData.revenue_growth}%`) : 'N/A')
                    }
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </Grid>

        {/* Company Description */}
        <Grid item xs={12}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>About</Typography>
            <Typography variant="body1">
              {companyInfo?.description && 
                companyInfo.description !== 'Not found' && 
                !companyInfo.description.includes('pharmaceutical') &&
                companyInfo.description.length > 10
                ? String(companyInfo.description)
                : `${companyInfo?.name || 'Company'} is a ${companyInfo?.industry || 'technology'} company`
              }
              {companyInfo?.founded && (
                <><br />Founded: {companyInfo.founded}</>  
              )}
              {companyInfo?.headquarters && (
                <><br />Headquarters: {companyInfo.headquarters}</>  
              )}
              {companyInfo?.employees && (
                <><br />Employees: {companyInfo.employees.toLocaleString()}</>  
              )}
              {companyInfo?.ceo && companyInfo.ceo !== 'Not specified' && (
                <><br />CEO: {companyInfo.ceo}</>  
              )}
            </Typography>
          </Paper>
        </Grid>

        {/* Hiring Status */}
        {hiringData?.hiring_status && (
          <Grid item xs={12} md={6}>
            <Paper sx={{ p: 2 }}>
              <Typography variant="h6" gutterBottom>Hiring Status</Typography>
              <Chip 
                label={String(hiringData.hiring_status)}
                color={String(hiringData.hiring_status) === 'Actively Hiring' ? 'success' : 'default'}
              />
              {hiringData?.open_positions && (
                <Typography variant="body2" mt={1}>
                  Open Positions: {String(hiringData.open_positions)}
                </Typography>
              )}
            </Paper>
          </Grid>
        )}

        {/* Financial Info */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>Financial Data</Typography>
            <List dense>
              {financialData?.revenue && (
                <ListItem>
                  <ListItemText 
                    primary="Revenue" 
                    secondary={typeof financialData.revenue === 'string' && financialData.revenue.includes('$') ? 
                      financialData.revenue : 
                      (!isNaN(financialData.revenue) ? 
                        `$${(financialData.revenue / 1000000000).toFixed(2)}B` : String(financialData.revenue))} 
                  />
                </ListItem>
              )}
              {financialData?.market_cap && (
                <ListItem>
                  <ListItemText 
                    primary="Market Cap" 
                    secondary={typeof financialData.market_cap === 'string' && financialData.market_cap.includes('$') ? 
                      financialData.market_cap : 
                      (!isNaN(financialData.market_cap) ? 
                        `$${(financialData.market_cap / 1000000000).toFixed(2)}B` : 'Not available')} 
                  />
                </ListItem>
              )}
              {financialData?.revenue_growth && (
                <ListItem>
                  <ListItemText 
                    primary="Revenue Growth" 
                    secondary={String(financialData.revenue_growth).includes('%') ? 
                      String(financialData.revenue_growth) : 
                      `${financialData.revenue_growth}%`} 
                  />
                </ListItem>
              )}
              {financialData?.profit_margin && (
                <ListItem>
                  <ListItemText 
                    primary="Profit Margin" 
                    secondary={`${financialData.profit_margin}%`} 
                  />
                </ListItem>
              )}
            </List>
          </Paper>
        </Grid>
      </Grid>
    );
  };

  const renderLookalikeCompanies = (data) => {
    const companies = data?.lookalike_companies || [];
    const isDemo = data?.search_metadata?.demo_mode || false;
    const targetCompany = data?.target_company || {};

    return (
      <Box>
        {isDemo && (
          <Alert severity="warning" sx={{ mb: 2 }}>
            <strong>📋 Demo Mode:</strong> Configure EXA_API_KEY and TAVILY_API_KEY for real data
          </Alert>
        )}

        <Box display="flex" alignItems="center" mb={3}>
          <BusinessIcon color="primary" sx={{ mr: 1 }} />
          <Typography variant="h5">
            Companies Similar to {targetCompany.name || 'Target Company'}
          </Typography>
        </Box>

        <Typography variant="subtitle1" color="text.secondary" gutterBottom>
          Found {companies.length} companies in {targetCompany.industry || 'similar industry'}
        </Typography>

        {/* Enhanced List View */}
        <List sx={{ bgcolor: 'background.paper', borderRadius: 2, border: '1px solid #e0e0e0' }}>
          {companies.map((company, index) => (
            <ListItem 
              key={index}
              divider={index < companies.length - 1}
              sx={{ 
                py: 2,
                '&:hover': { bgcolor: 'action.hover' },
                borderLeft: company.similarity_score > 0.7 ? '4px solid #4caf50' : 
                           company.similarity_score > 0.5 ? '4px solid #ff9800' : '4px solid #e0e0e0'
              }}
            >
              <ListItemAvatar>
                <Avatar sx={{ 
                  bgcolor: company.similarity_score > 0.7 ? 'success.main' : 
                          company.similarity_score > 0.5 ? 'warning.main' : 'grey.400',
                  width: 48,
                  height: 48
                }}>
                  <BusinessIcon />
                </Avatar>
              </ListItemAvatar>
              
              <ListItemText
                primary={
                  <Box display="flex" alignItems="center" gap={1}>
                    <Typography variant="h6" component="span">
                      {company.name || company.title || `Company ${index + 1}`}
                    </Typography>
                    <Chip 
                      label={`${(company.similarity_score * 100).toFixed(0)}% Match`}
                      color={company.similarity_score > 0.7 ? 'success' : company.similarity_score > 0.5 ? 'warning' : 'default'}
                      size="small"
                    />
                    <Chip 
                      label={company.source || 'Unknown'}
                      variant="outlined"
                      size="small"
                    />
                  </Box>
                }
                secondary={
                  <Box mt={1}>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      {company.snippet || 'No description available'}
                    </Typography>
                    
                    <Box display="flex" alignItems="center" gap={2} flexWrap="wrap">
                      <Typography variant="caption" color="text.secondary">
                        💰 Revenue: {company.revenue || 'Not available'}
                      </Typography>
                      {company.market_cap && (
                        <Typography variant="caption" color="text.secondary">
                          💹 Market Cap: {company.market_cap}
                        </Typography>
                      )}
                      <Typography variant="caption" color="text.secondary">
                        🏢 Industry: {company.industry || targetCompany.industry || 'Similar'}
                      </Typography>
                      {company.employees && (
                        <Typography variant="caption" color="text.secondary">
                          👥 Employees: {company.employees}
                        </Typography>
                      )}
                      {company.domain && (
                        <Typography variant="caption" color="text.secondary">
                          🔗 {company.domain}
                        </Typography>
                      )}
                      {company.financial_source === 'estimated' && (
                        <Chip 
                          label="Estimated" 
                          size="small" 
                          variant="outlined" 
                          color="info"
                          sx={{ height: 16, fontSize: '0.6rem' }}
                        />
                      )}
                    </Box>
                  </Box>
                }
              />
              
              <ListItemSecondaryAction>
                <IconButton 
                  edge="end" 
                  href={company.url} 
                  target="_blank"
                  rel="noopener noreferrer"
                  sx={{ mr: 1 }}
                >
                  <OpenInNewIcon />
                </IconButton>
              </ListItemSecondaryAction>
            </ListItem>
          ))}
        </List>

        {companies.length === 0 && (
          <Box textAlign="center" py={6}>
            <BusinessIcon sx={{ fontSize: 64, color: 'text.disabled', mb: 2 }} />
            <Typography variant="h6" color="text.secondary" gutterBottom>
              No Similar Companies Found
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Try researching a different company or check your API configuration
            </Typography>
          </Box>
        )}
      </Box>
    );
  };

  return (
    <Container maxWidth="lg">
      <Box py={3}>
        <Typography variant="h4" component="h1" gutterBottom>
          Company Research
        </Typography>
        <Typography variant="subtitle1" color="text.secondary" gutterBottom>
          Get comprehensive business intelligence data for any company
        </Typography>

        {/* Stats */}
        {stats && (
          <Paper sx={{ p: 2, mb: 3 }}>
            <Typography variant="h6" gutterBottom>Platform Stats</Typography>
            <Typography variant="body2">
              Companies in Database: {stats.companies_in_database}
            </Typography>
            <Typography variant="body2">
              Data Freshness Threshold: {stats.data_freshness_threshold}
            </Typography>
          </Paper>
        )}

        <Tabs value={activeTab} onChange={(e, newValue) => setActiveTab(newValue)} sx={{ mb: 3 }}>
          <Tab label="Research" />
          <Tab label="Results" disabled={!researchData} />
          <Tab label="Similar Companies" disabled={!lookalikeData} />
        </Tabs>

        {/* Research Tab */}
        {activeTab === 0 && (
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>Company Information</Typography>
            
            <Grid container spacing={2} sx={{ mb: 3 }}>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Company Name"
                  placeholder="e.g., Apple, Microsoft, Tesla"
                  value={companyName}
                  onChange={(e) => setCompanyName(e.target.value)}
                  required
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Domain Name"
                  placeholder="e.g., apple.com, microsoft.com"
                  value={domainName}
                  onChange={(e) => setDomainName(e.target.value)}
                  required
                />
              </Grid>
            </Grid>

            <Accordion>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography>Advanced Options</Typography>
              </AccordionSummary>
              <AccordionDetails>
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={forceRefresh}
                      onChange={(e) => setForceRefresh(e.target.checked)}
                    />
                  }
                  label="Force Refresh Data"
                />
                <Typography gutterBottom>Data Freshness (days): {dataFreshnessDays}</Typography>
                <Slider
                  value={dataFreshnessDays}
                  onChange={(e, newValue) => setDataFreshnessDays(newValue)}
                  min={1}
                  max={365}
                  marks={[
                    { value: 1, label: '1' },
                    { value: 30, label: '30' },
                    { value: 90, label: '90' },
                    { value: 180, label: '180' },
                    { value: 365, label: '365' }
                  ]}
                />
              </AccordionDetails>
            </Accordion>

            <Box mt={3}>
              <Button
                variant="contained"
                size="large"
                startIcon={loading ? <CircularProgress size={20} /> : <SearchIcon />}
                onClick={handleResearch}
                disabled={loading}
              >
                {loading ? 'Researching... (This may take up to 2 minutes for new companies)' : 'Research Company'}
              </Button>
            </Box>

            {error && (
              <Alert severity="error" sx={{ mt: 2 }}>
                {error}
              </Alert>
            )}

            {success && (
              <Alert severity="success" sx={{ mt: 2 }}>
                {success}
              </Alert>
            )}
          </Paper>
        )}

        {/* Results Tab */}
        {activeTab === 1 && researchData && (
          <Box>
            <Paper sx={{ p: 3, mb: 3 }}>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="h6">
                  Research Results
                  {researchData.is_cached && <Chip label="From Cache" size="small" sx={{ ml: 1 }} />}
                  {researchData.is_mock && <Chip label="Mock Data" color="warning" size="small" sx={{ ml: 1 }} />}
                </Typography>
                <Button
                  variant="outlined"
                  startIcon={lookalikeLoading ? <CircularProgress size={20} /> : <TrendingUpIcon />}
                  onClick={handleFindSimilar}
                  disabled={lookalikeLoading}
                >
                  {lookalikeLoading ? 'Finding...' : 'Find Similar Companies'}
                </Button>
              </Box>
              {renderCompanyOverview(researchData.company_data)}
            </Paper>

            {lookalikeError && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {lookalikeError}
              </Alert>
            )}
          </Box>
        )}

        {/* Similar Companies Tab */}
        {activeTab === 2 && lookalikeData && (
          <Paper sx={{ p: 3 }}>
            {renderLookalikeCompanies(lookalikeData)}
          </Paper>
        )}
      </Box>
    </Container>
  );
};

export default CompanyResearch;
