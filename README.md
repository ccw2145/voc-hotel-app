# Lakehouse Inn Voice of Customer

A GenAI-powered Voice of Customer application built on Databricks that continuously scans and interprets guest feedback across Lakehouse Inn's 120 hotel properties throughout the United States.

## Overview

Lakehouse Inn is a hospitality brand committed to delivering exceptional guest experiences. This application leverages advanced analytics and artificial intelligence to transform guest feedback into actionable insights, helping improve service quality and guest satisfaction across all properties.

## Technologies Used

- **Dash (Plotly)**: Interactive Python web application framework for the UI
- **Dash Bootstrap Components**: Modern, responsive UI components
- **FastAPI**: High-performance web framework for backend APIs (legacy)
- **Python-dotenv**: Environment variable management
- **Databricks SDK**: Integration with Databricks Lakehouse platform and Genie AI
- **Databricks SQL Connector**: Direct access to Delta tables via SQL warehouse
- **Unity Catalog**: Centralized data governance and table management
- **Pandas**: Data manipulation and analysis

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

## Data Sources

The application reads directly from Unity Catalog Delta tables in Databricks:

- **Issues Table**: Configurable via `DATABRICKS_CATALOG`, `DATABRICKS_SCHEMA`, and `ISSUES_TABLE_NAME` (defaults to `lakehouse_inn_catalog.voc.open_issues_diagnosis`)
  - Contains open issues identified across all properties
  - Tracks location, aspect, severity, status, volume, and more
  - Powers property diagnostics, flagged properties list, and recommendations
  - Updated in real-time as new issues are detected

All services use a shared `DatabaseService` that:
- Connects to Databricks SQL Warehouse for high-performance queries
- Implements connection pooling and 5-minute caching for optimal performance
- Authenticates using Databricks SDK credentials
- Supports both dictionary and pandas DataFrame output formats
- **Graceful fallback**: Automatically uses placeholder data if Databricks connection fails
  - Ensures app remains functional during development or connectivity issues
  - Warning messages displayed in terminal when using placeholder data

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
     - `DATABRICKS_SQL_WAREHOUSE_PATH` (SQL warehouse HTTP path, e.g., `/sql/1.0/warehouses/xxxxx`)
     - `LAKEBASE_INSTANCE_NAME`
     - `LAKEBASE_DB_NAME`
     - `MY_EMAIL`
     - `GENIE_SPACE_ID` (your Databricks Genie space ID)
     - `DATABRICKS_TOKEN` (optional - personal access token for Genie access)

3. Run the Dash application:
   ```bash
   python dash_app.py
   ```

4. Open your browser to `http://localhost:8000`

## Application Features

### Role Selection
Choose between two personas:
- **🏢 Headquarters**: View all properties, identify issues, and take action across the portfolio
- **🏨 Property Manager**: Monitor individual property performance and address guest feedback

### HQ Dashboard
- **Executive KPIs**: High-level metrics including average negative reviews, properties flagged, overall satisfaction, and reviews processed
- **Regional Performance Map**: Interactive US map showing all property locations, clickable to navigate to specific properties
- **Analytics & Insights**: 
  - Issue trend charts (30-day view)
  - Aspect breakdown analysis (top 10 issues)
  - Regional performance comparison (stacked bar charts)
- **Grouped Property View**: Properties organized by region with collapsible accordions
  - Critical and warning counts per region
  - Compact property cards within each region
  - Easy navigation between regions
- **Healthy Properties Summary**: Compact card showing count of healthy properties with expandable table view
- **Property Deep Dive**: Detailed analysis with aspect breakdowns, embedded Databricks dashboard, and reviews deep dive
- **Ask Genie AI**: Natural language queries about trends, issues, or comparisons
- **Automated Email Generation**: Generate detailed email communications to property managers with actionable recommendations

### Property Manager Dashboard  
- Select and monitor your specific property
- View detailed aspect performance metrics
- Ask Genie AI follow-up questions about your property
- Access real-time guest feedback insights

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

## Troubleshooting

### Using Placeholder Data

If you see messages like "📊 Using placeholder data for property service" in the terminal:

- The app is running with **mock data** because it cannot connect to Databricks
- The app remains fully functional with placeholder data for all features
- Common causes:
  - `DATABRICKS_SQL_WAREHOUSE_PATH` not set in `.env`
  - Invalid SQL warehouse path
  - Network connectivity issues
  - Incorrect Databricks credentials

### Verifying Database Connection

To verify your Databricks connection is working:

1. Check the terminal output when the app starts
2. If using **real data**, you'll see property names from your actual Delta table
3. If using **placeholder data**, you'll see warning messages and mock properties (Denver, Miami, Chicago, Austin, Seattle)

### Getting Help

- Check that all environment variables are set correctly in `.env`
- Verify your SQL warehouse is running in Databricks
- Ensure your service principal has proper permissions:
  - `CAN USE` on the SQL warehouse
  - `SELECT` permission on your configured Unity Catalog tables (default: `lakehouse_inn_catalog.voc.*`)

## Lakehouse Inn Brand

Lakehouse Inn operates 120 hotel properties across the United States, committed to providing exceptional hospitality experiences. This Voice of Customer application represents our investment in data-driven guest satisfaction and operational excellence.

### Mission
Transform guest feedback into exceptional hospitality experiences through advanced analytics and artificial intelligence.

### Vision  
Be the hospitality industry leader in guest satisfaction through data-driven insights and continuous improvement.