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

const ModelTweaking = () => {
  // State for loading
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(null);
  
  // Set a welcome message on component mount
  useEffect(() => {
    setMessage({
      type: 'info',
      text: 'Model tweaking feature is coming soon!'
    });
  }, []);
  
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
      
      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          Coming Soon
        </Typography>
        <Typography variant="body1" paragraph>
          The model tweaking feature will allow you to customize the scoring weights used to evaluate companies.
        </Typography>
        <Typography variant="body1" paragraph>
          You'll be able to adjust weights for factors like:
        </Typography>
        <ul>
          <li>Hiring signals</li>
          <li>Funding information</li>
          <li>Industry match</li>
          <li>Domain quality</li>
          <li>Company size</li>
          <li>Growth rate</li>
        </ul>
        <Typography variant="body1">
          Check back soon for this feature!
        </Typography>
      </Paper>
      
      {loading && <CircularProgress />}
    </Container>
  );
};

export default ModelTweaking;
