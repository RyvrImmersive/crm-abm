import React, { useState, useEffect } from 'react';
import { 
  Container, 
  Typography, 
  Grid, 
  Paper, 
  Box, 
  Card, 
  CardContent, 
  CardHeader,
  Button,
  CircularProgress
} from '@mui/material';
// Using direct fetch for API calls instead of non-existent services

const Dashboard = () => {
  const [stats, setStats] = useState({
    schedulerStatus: 'unknown',
    lastUpdate: null,
    companiesProcessed: 0,
    successRate: 0
  });
  const [loading, setLoading] = useState(true);

  // Fetch dashboard data
  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true);
        // Use our new company research API health check
        const response = await fetch('http://localhost:8000/api/health');
        const data = await response.json();
        
        // Update stats with available data
        setStats({
          schedulerStatus: data.success ? 'healthy' : 'error',
          lastUpdate: new Date().toISOString(),
          companiesProcessed: data.data?.companies_in_db === 'Available' ? 'Available' : 0,
          successRate: data.success ? 100 : 0
        });
      } catch (error) {
        console.error('Error fetching dashboard data:', error);
        // Set fallback data
        setStats({
          schedulerStatus: 'error',
          lastUpdate: null,
          companiesProcessed: 0,
          successRate: 0
        });
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
    // Refresh every 30 seconds
    const interval = setInterval(fetchDashboardData, 30000);
    return () => clearInterval(interval);
  }, []);

  // Handle scheduler start/stop (disabled - no scheduler API available)
  const handleSchedulerToggle = async () => {
    alert('Scheduler controls not available in this version');
  };

  // Process a test company (redirect to Company Research)
  const handleProcessTestCompany = async () => {
    alert('Use the Company Research tab to research companies!');
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>
      
      {loading ? (
        <Box display="flex" justifyContent="center" my={4}>
          <CircularProgress />
        </Box>
      ) : (
        <>
          <Grid container spacing={3}>
            {/* Scheduler Status */}
            <Grid item xs={12} md={6} lg={3}>
              <Paper
                sx={{
                  p: 2,
                  display: 'flex',
                  flexDirection: 'column',
                  height: 140,
                }}
              >
                <Typography component="h2" variant="h6" color="primary" gutterBottom>
                  Scheduler Status
                </Typography>
                <Typography component="p" variant="h4">
                  {stats.schedulerStatus ? String(stats.schedulerStatus).toUpperCase() : 'UNKNOWN'}
                </Typography>
                <Box sx={{ mt: 2 }}>
                  <Button 
                    variant="contained" 
                    color={stats.schedulerStatus === 'running' ? 'error' : 'success'}
                    onClick={handleSchedulerToggle}
                  >
                    {stats.schedulerStatus === 'running' ? 'Stop' : 'Start'}
                  </Button>
                </Box>
              </Paper>
            </Grid>
            
            {/* Last Update */}
            <Grid item xs={12} md={6} lg={3}>
              <Paper
                sx={{
                  p: 2,
                  display: 'flex',
                  flexDirection: 'column',
                  height: 140,
                }}
              >
                <Typography component="h2" variant="h6" color="primary" gutterBottom>
                  Last Update
                </Typography>
                <Typography component="p" variant="h4">
                  {stats.lastUpdate ? new Date(stats.lastUpdate).toLocaleString() : 'Never'}
                </Typography>
              </Paper>
            </Grid>
            
            {/* Companies Processed */}
            <Grid item xs={12} md={6} lg={3}>
              <Paper
                sx={{
                  p: 2,
                  display: 'flex',
                  flexDirection: 'column',
                  height: 140,
                }}
              >
                <Typography component="h2" variant="h6" color="primary" gutterBottom>
                  Companies Processed
                </Typography>
                <Typography component="p" variant="h4">
                  {stats.companiesProcessed}
                </Typography>
              </Paper>
            </Grid>
            
            {/* Success Rate */}
            <Grid item xs={12} md={6} lg={3}>
              <Paper
                sx={{
                  p: 2,
                  display: 'flex',
                  flexDirection: 'column',
                  height: 140,
                }}
              >
                <Typography component="h2" variant="h6" color="primary" gutterBottom>
                  Success Rate
                </Typography>
                <Typography component="p" variant="h4">
                  {stats.successRate}%
                </Typography>
              </Paper>
            </Grid>
            
            {/* Quick Actions */}
            <Grid item xs={12}>
              <Card>
                <CardHeader title="Quick Actions" />
                <CardContent>
                  <Grid container spacing={2}>
                    <Grid item>
                      <Button 
                        variant="contained" 
                        onClick={handleProcessTestCompany}
                        disabled={loading}
                      >
                        Process Test Company
                      </Button>
                    </Grid>
                    <Grid item>
                      <Button 
                        variant="contained" 
                        onClick={() => alert('HubSpot integration not available in this version')}
                        disabled={loading}
                      >
                        Create HubSpot Properties
                      </Button>
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </>
      )}
    </Container>
  );
};

export default Dashboard;
