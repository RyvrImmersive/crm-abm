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
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel
} from '@mui/material';
import { schedulerApi } from '../services/api';

const Scheduler = () => {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [newTask, setNewTask] = useState({
    name: '',
    task_type: 'clay_sync',
    interval: 3600,
    enabled: true,
    parameters: {
      domains: []
    }
  });
  const [schedulerStatus, setSchedulerStatus] = useState('stopped');

  // Fetch scheduler status and tasks
  useEffect(() => {
    const fetchSchedulerData = async () => {
      try {
        setLoading(true);
        const response = await schedulerApi.getStatus();
        setSchedulerStatus(response.data.status);
        setTasks(response.data.tasks || []);
      } catch (error) {
        console.error('Error fetching scheduler data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchSchedulerData();
    // Refresh every 30 seconds
    const interval = setInterval(fetchSchedulerData, 30000);
    return () => clearInterval(interval);
  }, []);

  // Handle scheduler start/stop
  const handleSchedulerToggle = async () => {
    try {
      setLoading(true);
      if (schedulerStatus === 'running') {
        await schedulerApi.stop();
        setSchedulerStatus('stopped');
      } else {
        await schedulerApi.start();
        setSchedulerStatus('running');
      }
    } catch (error) {
      console.error('Error toggling scheduler:', error);
    } finally {
      setLoading(false);
    }
  };

  // Handle adding a new task
  const handleAddTask = async () => {
    try {
      setLoading(true);
      await schedulerApi.addTask(newTask);
      setDialogOpen(false);
      
      // Refresh tasks
      const response = await schedulerApi.getStatus();
      setTasks(response.data.tasks || []);
      
      // Reset form
      setNewTask({
        name: '',
        task_type: 'clay_sync',
        interval: 3600,
        enabled: true,
        parameters: {
          domains: []
        }
      });
    } catch (error) {
      console.error('Error adding task:', error);
      alert('Error adding task. See console for details.');
    } finally {
      setLoading(false);
    }
  };

  // Handle removing a task
  const handleRemoveTask = async (taskId) => {
    try {
      setLoading(true);
      await schedulerApi.removeTask(taskId);
      
      // Refresh tasks
      const response = await schedulerApi.getStatus();
      setTasks(response.data.tasks || []);
    } catch (error) {
      console.error('Error removing task:', error);
      alert('Error removing task. See console for details.');
    } finally {
      setLoading(false);
    }
  };

  // Format interval for display
  const formatInterval = (seconds) => {
    if (seconds < 60) {
      return `${seconds} seconds`;
    } else if (seconds < 3600) {
      return `${Math.floor(seconds / 60)} minutes`;
    } else if (seconds < 86400) {
      return `${Math.floor(seconds / 3600)} hours`;
    } else {
      return `${Math.floor(seconds / 86400)} days`;
    }
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Typography variant="h4">
          Scheduler
        </Typography>
        <Box>
          <Button 
            variant="contained" 
            color={schedulerStatus === 'running' ? 'error' : 'success'}
            onClick={handleSchedulerToggle}
            disabled={loading}
            sx={{ mr: 2 }}
          >
            {schedulerStatus === 'running' ? 'Stop Scheduler' : 'Start Scheduler'}
          </Button>
          <Button 
            variant="contained" 
            onClick={() => setDialogOpen(true)}
            disabled={loading}
          >
            Add Task
          </Button>
        </Box>
      </Box>
      
      {loading ? (
        <Box display="flex" justifyContent="center" my={4}>
          <CircularProgress />
        </Box>
      ) : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Name</TableCell>
                <TableCell>Type</TableCell>
                <TableCell>Interval</TableCell>
                <TableCell>Last Run</TableCell>
                <TableCell>Next Run</TableCell>
                <TableCell>Status</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {tasks.length > 0 ? (
                tasks.map((task) => (
                  <TableRow key={task.id}>
                    <TableCell>{task.name}</TableCell>
                    <TableCell>{task.task_type}</TableCell>
                    <TableCell>{formatInterval(task.interval)}</TableCell>
                    <TableCell>
                      {task.last_run ? new Date(task.last_run).toLocaleString() : 'Never'}
                    </TableCell>
                    <TableCell>
                      {task.next_run ? new Date(task.next_run).toLocaleString() : 'Not scheduled'}
                    </TableCell>
                    <TableCell>
                      <Box 
                        sx={{ 
                          backgroundColor: task.enabled ? 'success.main' : 'error.main',
                          color: 'white',
                          borderRadius: 1,
                          px: 1,
                          py: 0.5,
                          display: 'inline-block'
                        }}
                      >
                        {task.enabled ? 'Enabled' : 'Disabled'}
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Button 
                        variant="outlined" 
                        color="error" 
                        size="small"
                        onClick={() => handleRemoveTask(task.id)}
                      >
                        Remove
                      </Button>
                    </TableCell>
                  </TableRow>
                ))
              ) : (
                <TableRow>
                  <TableCell colSpan={7} align="center">
                    No scheduled tasks found
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>
      )}
      
      {/* Add Task Dialog */}
      <Dialog 
        open={dialogOpen} 
        onClose={() => setDialogOpen(false)}
        fullWidth
        maxWidth="sm"
      >
        <DialogTitle>Add Scheduled Task</DialogTitle>
        <DialogContent>
          <Box component="form" sx={{ mt: 2 }}>
            <Grid container spacing={2}>
              <Grid item xs={12}>
                <TextField
                  label="Task Name"
                  fullWidth
                  value={newTask.name}
                  onChange={(e) => setNewTask({ ...newTask, name: e.target.value })}
                  required
                />
              </Grid>
              <Grid item xs={12}>
                <FormControl fullWidth>
                  <InputLabel>Task Type</InputLabel>
                  <Select
                    value={newTask.task_type}
                    onChange={(e) => setNewTask({ ...newTask, task_type: e.target.value })}
                  >
                    <MenuItem value="clay_sync">Clay Sync</MenuItem>
                    <MenuItem value="hubspot_update">HubSpot Update</MenuItem>
                    <MenuItem value="score_update">Score Update</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12}>
                <FormControl fullWidth>
                  <InputLabel>Interval</InputLabel>
                  <Select
                    value={newTask.interval}
                    onChange={(e) => setNewTask({ ...newTask, interval: e.target.value })}
                  >
                    <MenuItem value={300}>5 minutes</MenuItem>
                    <MenuItem value={900}>15 minutes</MenuItem>
                    <MenuItem value={1800}>30 minutes</MenuItem>
                    <MenuItem value={3600}>1 hour</MenuItem>
                    <MenuItem value={7200}>2 hours</MenuItem>
                    <MenuItem value={14400}>4 hours</MenuItem>
                    <MenuItem value={28800}>8 hours</MenuItem>
                    <MenuItem value={43200}>12 hours</MenuItem>
                    <MenuItem value={86400}>1 day</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12}>
                <TextField
                  label="Domains (comma separated)"
                  fullWidth
                  helperText="Leave empty to process all companies"
                  value={newTask.parameters.domains.join(', ')}
                  onChange={(e) => setNewTask({ 
                    ...newTask, 
                    parameters: { 
                      ...newTask.parameters, 
                      domains: e.target.value.split(',').map(d => d.trim()).filter(d => d) 
                    } 
                  })}
                />
              </Grid>
              <Grid item xs={12}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={newTask.enabled}
                      onChange={(e) => setNewTask({ ...newTask, enabled: e.target.checked })}
                    />
                  }
                  label="Enabled"
                />
              </Grid>
            </Grid>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Cancel</Button>
          <Button 
            onClick={handleAddTask} 
            disabled={!newTask.name || loading}
            variant="contained"
          >
            Add Task
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default Scheduler;
