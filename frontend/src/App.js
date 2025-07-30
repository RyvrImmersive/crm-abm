import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme, CssBaseline, Box } from '@mui/material';
import './App.css';

// Import components
import Navigation from './components/Navigation';

// Import pages
import Dashboard from './pages/Dashboard';
import Companies from './pages/Companies';
import CompanyResearch from './pages/CompanyResearch';
import Scheduler from './pages/Scheduler';
import Settings from './pages/Settings';
import ModelTweaking from './pages/ModelTweaking';

// Create a theme
const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
    background: {
      default: '#f5f5f5',
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
          <Navigation />
          <Box component="main" sx={{ flexGrow: 1, py: 3 }}>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/companies" element={<Companies />} />
              <Route path="/company-research" element={<CompanyResearch />} />
              <Route path="/scheduler" element={<Scheduler />} />
              <Route path="/model-tweaking" element={<ModelTweaking />} />
              <Route path="/settings" element={<Settings />} />
            </Routes>
          </Box>
        </Box>
      </Router>
    </ThemeProvider>
  );
}

export default App;
