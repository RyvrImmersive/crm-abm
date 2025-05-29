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
import { clayApi, schedulerApi } from '../services/api';

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
        // Get scheduler status
        const schedulerResponse = await schedulerApi.getStatus();
        
        // Update stats
        setStats({
          schedulerStatus: schedulerResponse.data.status,
          lastUpdate: schedulerResponse.data.last_run,
          companiesProcessed: schedulerResponse.data.processed_count || 0,
          successRate: schedulerResponse.data.success_rate || 0
        });
      } catch (error) {
        console.error('Error fetching dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
    // Refresh every 30 seconds
    const interval = setInterval(fetchDashboardData, 30000);
    return () => clearInterval(interval);
  }, []);

  // Handle scheduler start/stop
  const handleSchedulerToggle = async () => {
    try {
      if (stats.schedulerStatus === 'running') {
        await schedulerApi.stop();
        setStats({ ...stats, schedulerStatus: 'stopped' });
      } else {
        await schedulerApi.start();
        setStats({ ...stats, schedulerStatus: 'running' });
      }
    } catch (error) {
      console.error('Error toggling scheduler:', error);
    }
  };

  // Process a test company
  const handleProcessTestCompany = async () => {
    try {
      setLoading(true);
      await clayApi.processCompany('example.com');
      alert('Test company processing initiated!');
    } catch (error) {
      console.error('Error processing test company:', error);
      alert('Error processing test company. See console for details.');
    } finally {
      setLoading(false);
    }
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
                  {stats.schedulerStatus.toUpperCase()}
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
                        onClick={() => clayApi.createHubspotProperties()}
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
