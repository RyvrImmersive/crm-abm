import React, { useState, useEffect } from 'react';
import { 
  Container, 
  Typography, 
  Paper, 
  CircularProgress,
  Alert,
  Box,
  Slider,
  Button,
  Grid
} from '@mui/material';

const ModelTweaking = () => {
  // State for loading and messages
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(null);
  
  // State for weights
  const [weights, setWeights] = useState({
    hiring: 0.2,
    funding: 0.2,
    industry_match: 0.2,
    domain_quality: 0.1,
    positive_news: 0.1,
    company_size: 0.1,
    growth_rate: 0.1
  });
  
  // Set a welcome message on component mount
  useEffect(() => {
    setMessage({
      type: 'info',
      text: 'Adjust the weights below to customize the scoring model'
    });
  }, []);
  
  // Calculate total weight
  const totalWeight = Object.values(weights).reduce((sum, val) => sum + val, 0);
  
  // Handle weight change
  const handleWeightChange = (factor, value) => {
    setWeights(prev => ({
      ...prev,
      [factor]: value
    }));
  };
  
  // Save weights (mock function for now)
  const saveWeights = () => {
    setLoading(true);
    // Simulate API call
    setTimeout(() => {
      setLoading(false);
      setMessage({
        type: 'success',
        text: 'Weights saved successfully!'
      });
    }, 1000);
  };
  
  // Reset weights
  const resetWeights = () => {
    setWeights({
      hiring: 0.2,
      funding: 0.2,
      industry_match: 0.2,
      domain_quality: 0.1,
      positive_news: 0.1,
      company_size: 0.1,
      growth_rate: 0.1
    });
    setMessage({
      type: 'info',
      text: 'Weights reset to default values'
    });
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
      
      <Paper sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6">
            Scoring Model Weights
          </Typography>
          <Box>
            <Button 
              variant="outlined" 
              onClick={resetWeights} 
              sx={{ mr: 1 }}
              disabled={loading}
            >
              Reset
            </Button>
            <Button 
              variant="contained" 
              onClick={saveWeights} 
              disabled={loading || Math.abs(totalWeight - 1) > 0.01}
              color="primary"
            >
              Save
            </Button>
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
                <Typography id={`${factor}-slider`} sx={{ textTransform: 'capitalize', mr: 1, minWidth: 120 }}>
                  {factor.replace('_', ' ')}
                </Typography>
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
