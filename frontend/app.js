const express = require('express');
const axios = require('axios');
const path = require('node:path');
require('dotenv').config();

const app = express();
const PORT = process.env.FRONTEND_PORT || 3000;
const API_URL = process.env.API_URL || 'http://api:8000';

// Logging middleware
app.use((req, res, next) => {
    console.log(`${new Date().toISOString()} - ${req.method} ${req.path}`);
    next();
});

app.use(express.json());
app.use(express.static(path.join(__dirname, 'views')));

app.post('/submit', async (req, res) => {
    try {
        const response = await axios.post(`${API_URL}/jobs`, {}, {
            timeout: 5000,
            headers: { 'Content-Type': 'application/json' }
        });
        res.json(response.data);
    } catch (err) {
        console.error('Error submitting job:', err.message);
        if (err.response) {
            res.status(err.response.status).json({ 
                error: err.response.data.detail || "API error occurred"
            });
        } else if (err.request) {
            res.status(503).json({ error: "API service unavailable" });
        } else {
            res.status(500).json({ error: "Internal server error" });
        }
    }
});

app.get('/status/:id', async (req, res) => {
    try {
        const response = await axios.get(`${API_URL}/jobs/${req.params.id}`, {
            timeout: 5000
        });
        res.json(response.data);
    } catch (err) {
        console.error('Error checking status:', err.message);
        if (err.response?.status === 404) {
            res.status(404).json({ error: "Job not found" });
        } else if (err.response) {
            res.status(err.response.status).json({ 
                error: err.response.data.detail || "API error occurred"
            });
        } else if (err.request) {
            res.status(503).json({ error: "API service unavailable" });
        } else {
            res.status(500).json({ error: "Internal server error" });
        }
    }
});

// Health check endpoint
app.get('/health', (req, res) => {
    res.json({ status: 'healthy', service: 'frontend', timestamp: new Date().toISOString() });
});

// Root endpoint
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'views', 'index.html'));
});

const server = app.listen(PORT, () => {
    console.log(`Frontend running on port ${PORT}`);
    console.log(`API URL: ${API_URL}`);
});

// Graceful shutdown
process.on('SIGTERM', () => {
    console.log('SIGTERM received, closing server...');
    server.close(() => {
        console.log('Server closed');
        process.exit(0);
    });
});

process.on('SIGINT', () => {
    console.log('SIGINT received, closing server...');
    server.close(() => {
        console.log('Server closed');
        process.exit(0);
    });
});
