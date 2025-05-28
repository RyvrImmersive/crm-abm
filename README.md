# ABM CRM System

A CRM system for Account-Based Marketing with HubSpot integration and AstraDB storage.

## Features
- HubSpot webhook integration
- Entity scoring
- AstraDB persistence
- RESTful API

## Setup
1. Clone the repository
2. Configure environment variables in .env
3. Run with Docker: `docker-compose up`

## API Endpoints
- `/`: API information
- `/health`: Health check
- `/hubspot-webhook`: Process HubSpot webhooks
- `/cache/stats`: Get cache statistics
- `/cache/clear`: Clear cache
- `/flow/status`: Get flow status
