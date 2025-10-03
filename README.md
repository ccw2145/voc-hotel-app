# Lakehouse Inn Voice of Customer

A GenAI-powered Voice of Customer application built on Databricks that continuously scans and interprets guest feedback across Lakehouse Inn's 120 hotel properties throughout the United States.

## Overview

Lakehouse Inn is a hospitality brand committed to delivering exceptional guest experiences. This application leverages advanced analytics and artificial intelligence to transform guest feedback into actionable insights, helping improve service quality and guest satisfaction across all properties.

## Technologies Used

- **FastAPI**: High-performance web framework for building APIs
- **Uvicorn**: ASGI server for running the FastAPI application  
- **Python-dotenv**: Environment variable management
- **Databricks SDK**: Integration with Databricks Lakehouse platform
- **PostgreSQL**: Database backend via psycopg2
- **HTML5/CSS3**: Modern, responsive frontend design

## Key Features

### 🎯 Voice of Customer Analytics
- **Real-time Monitoring**: Continuous scanning of guest feedback across all channels
- **GenAI Processing**: Advanced natural language processing for sentiment analysis
- **Trend Identification**: Automated detection of emerging patterns and concerns
- **Multi-property Insights**: Property-specific and brand-wide analytics
- **Alert System**: Automated notifications for critical guest concerns

### 🏨 Hospitality Focus
- **120 Properties**: Comprehensive coverage across all Lakehouse Inn locations
- **Guest-Centric**: Designed to enhance guest experience and satisfaction
- **Operational Intelligence**: Actionable insights for property management teams
- **Brand Consistency**: Ensuring uniform service excellence across all locations

### 🔒 Enterprise Security
- **Databricks Integration**: Secure connection to enterprise data platform
- **Environment Configuration**: Secure credential management
- **Schema Isolation**: Data separation and access controls
- **Compliance Ready**: Built with hospitality industry standards in mind

## Getting Started

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up environment variables:
   - Copy `example.env` to `.env`
   - Fill in your actual Databricks credentials:
     - `DATABRICKS_HOST`
     - `DATABRICKS_CLIENT_ID` 
     - `DATABRICKS_CLIENT_SECRET`
     - `LAKEBASE_INSTANCE_NAME`
     - `LAKEBASE_DB_NAME`
     - `MY_EMAIL`

3. Run the application:
   ```bash
   python app.py
   ```

4. Open your browser to `http://localhost:8000`

## API Endpoints

### System
- `GET /` - Main application dashboard
- `GET /health` - Health check endpoint

*Additional endpoints for feedback analysis, reporting, and property management will be added in subsequent iterations.*

## Architecture

### Databricks Integration
- **Lakehouse Platform**: Leverages Databricks' unified analytics platform
- **GenAI Capabilities**: Uses advanced AI models for natural language processing
- **Scalable Processing**: Handles feedback from 120+ properties efficiently
- **Real-time Analytics**: Continuous processing and insight generation

### Connection Management
- **Singleton Pattern**: Efficient connection pooling with automatic token refresh
- **OAuth Integration**: Seamless Databricks authentication
- **Token Refresh**: Automatic renewal every 59 minutes
- **Connection Pooling**: Optimized database connections

## Lakehouse Inn Brand

Lakehouse Inn operates 120 hotel properties across the United States, committed to providing exceptional hospitality experiences. This Voice of Customer application represents our investment in data-driven guest satisfaction and operational excellence.

### Mission
Transform guest feedback into exceptional hospitality experiences through advanced analytics and artificial intelligence.

### Vision  
Be the hospitality industry leader in guest satisfaction through data-driven insights and continuous improvement.