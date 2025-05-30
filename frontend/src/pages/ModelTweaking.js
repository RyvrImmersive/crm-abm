import React, { useState, useEffect } from 'react';
import { 
  Container, 
  Typography, 
  Grid, 
  Paper, 
  Box, 
  Slider, 
  Button,
  Card,
  CardContent,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  CircularProgress,
  Alert,
  Divider,
  Tooltip,
  IconButton,
  Chip
} from '@mui/material';
import { scoringApi } from '../services/api';
import InfoIcon from '@mui/icons-material/Info';
import RestartAltIcon from '@mui/icons-material/RestartAlt';
import SaveIcon from '@mui/icons-material/Save';
import BarChartIcon from '@mui/icons-material/BarChart';

const ModelTweaking = () => {
  // State for weights
  const [weights, setWeights] = useState({
    hiring: 0.1,
    funding: 0.1,
    industry_match: 0.2,
    domain_quality: 0.15,
    positive_news: 0.15,
    company_size: 0.1,
    growth_rate: 0.1,
    tech_adoption: 0.1
  });
  
  // State for loading and messages
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(null);
  const [testCompany, setTestCompany] = useState({
    properties: {
      name: "Example Corp",
      domain: "example.com",
      industry: "Technology",
      description: "A tech company with recent funding and hiring initiatives"
    },
    hiring: true,
    funding: true
  });
  const [testResult, setTestResult] = useState(null);
  
  // Load weights on component mount
  useEffect(() => {
    fetchWeights();
  }, []);
  
  // Fetch current weights from API
  const fetchWeights = async () => {
    try {
      setLoading(true);
      const response = await scoringApi.getWeights();
      setWeights(response.data.weights);
      setMessage({
        type: 'success',
        text: 'Current model weights loaded successfully'
      });
    } catch (error) {
      console.error('Error fetching weights:', error);
      setMessage({
        type: 'error',
        text: 'Error loading model weights'
      });
    } finally {
      setLoading(false);
    }
  };
  
  // Handle weight change
  const handleWeightChange = (factor, value) => {
    setWeights(prev => ({
      ...prev,
      [factor]: value
    }));
  };
  
  // Save weights
  const saveWeights = async () => {
    try {
      setLoading(true);
      const response = await scoringApi.updateWeights(weights);
      setWeights(response.data.weights);
      setMessage({
        type: 'success',
        text: 'Model weights updated successfully'
      });
    } catch (error) {
      console.error('Error updating weights:', error);
      setMessage({
        type: 'error',
        text: 'Error updating model weights'
      });
    } finally {
      setLoading(false);
    }
  };
  
  // Reset weights to default
  const resetWeights = async () => {
    try {
      setLoading(true);
      const response = await scoringApi.resetWeights();
      setWeights(response.data.weights);
      setMessage({
        type: 'success',
        text: 'Model weights reset to default values'
      });
    } catch (error) {
      console.error('Error resetting weights:', error);
      setMessage({
        type: 'error',
        text: 'Error resetting model weights'
      });
    } finally {
      setLoading(false);
    }
  };
  
  // Test the model with current weights
  const testModel = async () => {
    try {
      setLoading(true);
      const response = await scoringApi.scoreEntity(testCompany, weights);
      setTestResult(response.data.score);
      setMessage({
        type: 'success',
        text: 'Test scoring completed'
      });
    } catch (error) {
      console.error('Error testing model:', error);
      setMessage({
        type: 'error',
        text: 'Error testing model'
      });
    } finally {
      setLoading(false);
    }
  };
  
  // Handle test company field change
  const handleTestCompanyChange = (field, value) => {
    setTestCompany(prev => ({
      ...prev,
      properties: {
        ...prev.properties,
        [field]: value
      }
    }));
  };
  
  // Handle boolean field change
  const handleBooleanChange = (field, value) => {
    setTestCompany(prev => ({
      ...prev,
      [field]: value
    }));
  };
  
  // Calculate total weight
  const totalWeight = Object.values(weights).reduce((sum, weight) => sum + weight, 0);
  
  // Weight factor descriptions
  const factorDescriptions = {
    hiring: "Importance of hiring signals in company description or data",
    funding: "Weight given to recent funding rounds or investment mentions",
    industry_match: "How much industry alignment matters to the score",
    domain_quality: "Impact of domain reputation and quality",
    positive_news: "Weight of positive news mentions",
    company_size: "Importance of company size in scoring",
    growth_rate: "How much growth indicators affect the score",
    tech_adoption: "Weight given to technology adoption signals"
  };
  
  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom>
        Model Tweaking
      </Typography>
      
      {message && (
        <Alert 
          severity={message.type} 
          sx={{ mb: 2 }}
          onClose={() => setMessage(null)}
        >
          {message.text}
        </Alert>
      )}
      
      <Grid container spacing={3}>
        {/* Weight Adjustment Section */}
        <Grid item xs={12} md={7}>
          <Paper sx={{ p: 3, height: '100%' }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">
                Scoring Model Weights
              </Typography>
              <Box>
                <Tooltip title="Reset to Default Weights">
                  <IconButton onClick={resetWeights} disabled={loading}>
                    <RestartAltIcon />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Save Changes">
                  <IconButton 
                    onClick={saveWeights} 
                    disabled={loading || Math.abs(totalWeight - 1) > 0.01}
                    color="primary"
                  >
                    <SaveIcon />
                  </IconButton>
                </Tooltip>
              </Box>
            </Box>
            
            <Alert 
              severity={Math.abs(totalWeight - 1) <= 0.01 ? "success" : "warning"} 
              sx={{ mb: 2 }}
            >
              Total weight: {totalWeight.toFixed(2)} {Math.abs(totalWeight - 1) > 0.01 && "(should be close to 1.0)"}
            </Alert>
            
            <Grid container spacing={2}>
              {Object.entries(weights).map(([factor, value]) => (
                <Grid item xs={12} key={factor}>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                    <Typography id={`${factor}-slider`} sx={{ textTransform: 'capitalize', mr: 1 }}>
                      {factor.replace('_', ' ')}
                    </Typography>
                    <Tooltip title={factorDescriptions[factor] || ""}>
                      <InfoIcon fontSize="small" color="action" />
                    </Tooltip>
                    <Box sx={{ ml: 'auto' }}>
                      <Typography variant="body2" color="text.secondary">
                        {value.toFixed(2)}
                      </Typography>
                    </Box>
                  </Box>
                  <Slider
                    value={value}
                    onChange={(e, newValue) => handleWeightChange(factor, newValue)}
                    aria-labelledby={`${factor}-slider`}
                    step={0.01}
                    min={0}
                    max={1}
                    disabled={loading}
                  />
                </Grid>
              ))}
            </Grid>
          </Paper>
        </Grid>
        
        {/* Test Model Section */}
        <Grid item xs={12} md={5}>
          <Paper sx={{ p: 3, height: '100%' }}>
            <Typography variant="h6" gutterBottom>
              Test Model
            </Typography>
            
            <Box sx={{ mb: 3 }}>
              <Typography variant="subtitle2" gutterBottom>
                Test Company Details
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={12}>
                  <TextField
                    label="Company Name"
                    fullWidth
                    value={testCompany.properties.name}
                    onChange={(e) => handleTestCompanyChange('name', e.target.value)}
                    margin="dense"
                    variant="outlined"
                    size="small"
                  />
                </Grid>
                <Grid item xs={12}>
                  <TextField
                    label="Domain"
                    fullWidth
                    value={testCompany.properties.domain}
                    onChange={(e) => handleTestCompanyChange('domain', e.target.value)}
                    margin="dense"
                    variant="outlined"
                    size="small"
                  />
                </Grid>
                <Grid item xs={12}>
                  <TextField
                    label="Industry"
                    fullWidth
                    value={testCompany.properties.industry}
                    onChange={(e) => handleTestCompanyChange('industry', e.target.value)}
                    margin="dense"
                    variant="outlined"
                    size="small"
                  />
                </Grid>
                <Grid item xs={12}>
                  <TextField
                    label="Description"
                    fullWidth
                    multiline
                    rows={2}
                    value={testCompany.properties.description}
                    onChange={(e) => handleTestCompanyChange('description', e.target.value)}
                    margin="dense"
                    variant="outlined"
                    size="small"
                  />
                </Grid>
                <Grid item xs={6}>
                  <FormControl fullWidth size="small">
                    <InputLabel>Hiring</InputLabel>
                    <Select
                      value={testCompany.hiring ? "true" : "false"}
                      onChange={(e) => handleBooleanChange('hiring', e.target.value === "true")}
                      label="Hiring"
                    >
                      <MenuItem value="true">Yes</MenuItem>
                      <MenuItem value="false">No</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={6}>
                  <FormControl fullWidth size="small">
                    <InputLabel>Recent Funding</InputLabel>
                    <Select
                      value={testCompany.funding ? "true" : "false"}
                      onChange={(e) => handleBooleanChange('funding', e.target.value === "true")}
                      label="Recent Funding"
                    >
                      <MenuItem value="true">Yes</MenuItem>
                      <MenuItem value="false">No</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
              </Grid>
              
              <Box sx={{ mt: 2, display: 'flex', justifyContent: 'center' }}>
                <Button
                  variant="contained"
                  startIcon={<BarChartIcon />}
                  onClick={testModel}
                  disabled={loading}
                >
                  Test Score
                </Button>
              </Box>
            </Box>
            
            <Divider sx={{ my: 2 }} />
            
            {/* Test Results */}
            {testResult && testResult.crm_score ? (
              <Box>
                <Typography variant="subtitle2" gutterBottom>
                  Test Results
                </Typography>
                <Card variant="outlined" sx={{ mb: 2 }}>
                  <CardContent>
                    <Typography variant="h4" color="primary" align="center">
                      {Math.round(testResult.crm_score * 100)}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" align="center">
                      Score out of 100
                    </Typography>
                  </CardContent>
                </Card>
                
                {testResult && testResult.components && testResult.components.signals && Array.isArray(testResult.components.signals) && (
                  <Box>
                    <Typography variant="subtitle2" gutterBottom>
                      Signals Detected
                    </Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                      {testResult.components.signals.map((signal, index) => (
                        <Chip 
                          key={index} 
                          label={signal} 
                          variant="outlined" 
                          size="small" 
                        />
                      ))}
                    </Box>
                  </Box>
                )}
              </Box>
            ) : (
              <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 200 }}>
                <Typography variant="body2" color="text.secondary">
                  Test the model to see results
                </Typography>
              </Box>
            )}
          </Paper>
        </Grid>
      </Grid>
      
      {loading && (
        <Box sx={{ 
          position: 'fixed', 
          top: 0, 
          left: 0, 
          right: 0, 
          bottom: 0, 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center',
          backgroundColor: 'rgba(0, 0, 0, 0.3)',
          zIndex: 9999
        }}>
          <CircularProgress />
        </Box>
      )}
    </Container>
  );
};

export default ModelTweaking;
