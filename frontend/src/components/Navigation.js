import React from 'react';
import { AppBar, Toolbar, Typography, Button, Box } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';

const Navigation = () => {
  return (
    <AppBar position="static">
      <Toolbar>
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          Clay-HubSpot Integration
        </Typography>
        <Box>
          <Button color="inherit" component={RouterLink} to="/">
            Dashboard
          </Button>
          <Button color="inherit" component={RouterLink} to="/companies">
            Companies
          </Button>
          <Button color="inherit" component={RouterLink} to="/scheduler">
            Scheduler
          </Button>
          <Button color="inherit" component={RouterLink} to="/model-tweaking">
            Model Tweaking
          </Button>
          <Button color="inherit" component={RouterLink} to="/settings">
            Settings
          </Button>
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default Navigation;
