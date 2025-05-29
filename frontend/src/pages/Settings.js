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
  Divider,
  Card,
  CardContent,
  CardHeader,
  Switch,
  FormControlLabel
} from '@mui/material';
import axios from 'axios';

const Settings = () => {
  const [settings, setSettings] = useState({
    hubspot_api_key: '',
    clay_api_key: '',
    clay_api_base_url: 'https://api.clay.com/v1',
    log_level: 'INFO',
    hubspot_cache_ttl: 3600,
    scoring_cache_ttl: 86400,
    prompt_cache_ttl: 3600
  });
  
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [status, setStatus] = useState({ type: '', message: '' });
  const [debugMode, setDebugMode] = useState(false);

  // Fetch current settings
  useEffect(() => {
    const fetchSettings = async () => {
      try {
        setLoading(true);
        // In a real app, you would fetch this from your API
        // For now, we'll just simulate it
        setTimeout(() => {
          // This would normally come from your API
          setSettings({
            hubspot_api_key: '••••••••••••••••••••••••••',
            clay_api_key: '••••••••••••••••',
            clay_api_base_url: 'https://api.clay.com/v1',
            log_level: 'INFO',
            hubspot_cache_ttl: 3600,
            scoring_cache_ttl: 86400,
            prompt_cache_ttl: 3600
          });
          setLoading(false);
        }, 1000);
      } catch (error) {
        console.error('Error fetching settings:', error);
        setStatus({
          type: 'error',
          message: 'Failed to load settings. Please try again.'
        });
        setLoading(false);
      }
    };

    fetchSettings();
  }, []);

  // Handle settings save
  const handleSaveSettings = async () => {
    try {
      setSaving(true);
      // In a real app, you would send this to your API
      // For now, we'll just simulate it
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      setStatus({
        type: 'success',
        message: 'Settings saved successfully!'
      });
    } catch (error) {
      console.error('Error saving settings:', error);
      setStatus({
        type: 'error',
        message: 'Failed to save settings. Please try again.'
      });
    } finally {
      setSaving(false);
    }
  };

  // Handle input change
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setSettings({
      ...settings,
      [name]: value
    });
  };

  // Handle numeric input change
  const handleNumericChange = (e) => {
    const { name, value } = e.target;
    setSettings({
      ...settings,
      [name]: parseInt(value, 10) || 0
    });
  };

  // Test connection to HubSpot
  const testHubSpotConnection = async () => {
    try {
      setSaving(true);
      // In a real app, you would test the connection through your API
      // For now, we'll just simulate it
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      setStatus({
        type: 'success',
        message: 'HubSpot connection successful!'
      });
    } catch (error) {
      console.error('Error testing HubSpot connection:', error);
      setStatus({
        type: 'error',
        message: 'Failed to connect to HubSpot. Please check your API key.'
      });
    } finally {
      setSaving(false);
    }
  };

  // Test connection to Clay
  const testClayConnection = async () => {
    try {
      setSaving(true);
      // In a real app, you would test the connection through your API
      // For now, we'll just simulate it
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      setStatus({
        type: 'success',
        message: 'Clay connection successful!'
      });
    } catch (error) {
      console.error('Error testing Clay connection:', error);
      setStatus({
        type: 'error',
        message: 'Failed to connect to Clay. Please check your API key and base URL.'
      });
    } finally {
      setSaving(false);
    }
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom>
        Settings
      </Typography>
      
      {status.message && (
        <Alert 
          severity={status.type} 
          sx={{ mb: 3 }}
          onClose={() => setStatus({ type: '', message: '' })}
        >
          {status.message}
        </Alert>
      )}
      
      {loading ? (
        <Box display="flex" justifyContent="center" my={4}>
          <CircularProgress />
        </Box>
      ) : (
        <Grid container spacing={3}>
          {/* API Keys */}
          <Grid item xs={12}>
            <Card>
              <CardHeader title="API Keys" />
              <CardContent>
                <Grid container spacing={3}>
                  <Grid item xs={12} md={6}>
                    <TextField
                      label="HubSpot API Key"
                      name="hubspot_api_key"
                      value={settings.hubspot_api_key}
                      onChange={handleInputChange}
                      fullWidth
                      type={debugMode ? "text" : "password"}
                      InputProps={{
                        endAdornment: (
                          <Button 
                            variant="outlined" 
                            size="small"
                            onClick={testHubSpotConnection}
                            disabled={saving}
                          >
                            Test
                          </Button>
                        ),
                      }}
                    />
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <TextField
                      label="Clay API Key"
                      name="clay_api_key"
                      value={settings.clay_api_key}
                      onChange={handleInputChange}
                      fullWidth
                      type={debugMode ? "text" : "password"}
                      InputProps={{
                        endAdornment: (
                          <Button 
                            variant="outlined" 
                            size="small"
                            onClick={testClayConnection}
                            disabled={saving}
                          >
                            Test
                          </Button>
                        ),
                      }}
                    />
                  </Grid>
                  <Grid item xs={12}>
                    <TextField
                      label="Clay API Base URL"
                      name="clay_api_base_url"
                      value={settings.clay_api_base_url}
                      onChange={handleInputChange}
                      fullWidth
                    />
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          </Grid>
          
          {/* Cache Settings */}
          <Grid item xs={12}>
            <Card>
              <CardHeader title="Cache Settings" />
              <CardContent>
                <Grid container spacing={3}>
                  <Grid item xs={12} md={4}>
                    <TextField
                      label="HubSpot Cache TTL (seconds)"
                      name="hubspot_cache_ttl"
                      value={settings.hubspot_cache_ttl}
                      onChange={handleNumericChange}
                      fullWidth
                      type="number"
                    />
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <TextField
                      label="Scoring Cache TTL (seconds)"
                      name="scoring_cache_ttl"
                      value={settings.scoring_cache_ttl}
                      onChange={handleNumericChange}
                      fullWidth
                      type="number"
                    />
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <TextField
                      label="Prompt Cache TTL (seconds)"
                      name="prompt_cache_ttl"
                      value={settings.prompt_cache_ttl}
                      onChange={handleNumericChange}
                      fullWidth
                      type="number"
                    />
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          </Grid>
          
          {/* Logging Settings */}
          <Grid item xs={12}>
            <Card>
              <CardHeader title="Logging Settings" />
              <CardContent>
                <Grid container spacing={3}>
                  <Grid item xs={12} md={6}>
                    <TextField
                      label="Log Level"
                      name="log_level"
                      value={settings.log_level}
                      onChange={handleInputChange}
                      select
                      fullWidth
                      SelectProps={{
                        native: true,
                      }}
                    >
                      <option value="DEBUG">DEBUG</option>
                      <option value="INFO">INFO</option>
                      <option value="WARNING">WARNING</option>
                      <option value="ERROR">ERROR</option>
                    </TextField>
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={debugMode}
                          onChange={(e) => setDebugMode(e.target.checked)}
                        />
                      }
                      label="Debug Mode (Show API Keys)"
                    />
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          </Grid>
          
          {/* Save Button */}
          <Grid item xs={12}>
            <Box display="flex" justifyContent="flex-end">
              <Button
                variant="contained"
                color="primary"
                onClick={handleSaveSettings}
                disabled={saving}
                sx={{ mt: 2 }}
              >
                {saving ? 'Saving...' : 'Save Settings'}
              </Button>
            </Box>
          </Grid>
        </Grid>
      )}
    </Container>
  );
};

export default Settings;
