# Databricks Apps Deployment Guide

This guide walks through deploying the Lakehouse Inn Voice of Customer application to Databricks Apps.

## Prerequisites

### 1. Databricks Workspace Setup
- [ ] Databricks workspace with Apps feature enabled
- [ ] Databricks CLI installed and configured
- [ ] Workspace admin access or appropriate permissions

### 2. Service Principal Configuration
- [ ] Service principal created in Databricks
- [ ] Client ID and Client Secret obtained
- [ ] Service principal added to workspace

### 3. Required Permissions
Ensure your service principal has:
- [ ] `CAN USE` permission on SQL Warehouse
- [ ] `SELECT` permission on Unity Catalog tables:
  - `lakehouse_inn_catalog.voc.open_issues_diagnosis`
  - `lakehouse_inn_catalog.voc.review_aspect_details`
  - `lakehouse_inn_catalog.voc.hotel_locations`
- [ ] Access to Lakebase OLTP instance (`fe_shared_demo`)
- [ ] Access to Genie Space

### 4. Resources Configured
- [ ] SQL Warehouse running and accessible
- [ ] Genie Space ID obtained from Databricks UI
- [ ] Lakebase OLTP instance provisioned

## Deployment Steps

### Step 1: Configure Secrets

Store sensitive values in Databricks Secrets:

```bash
# Create a secret scope (if not exists)
databricks secrets create-scope --scope voc-app

# Store the service principal secret
databricks secrets put --scope voc-app --key client-secret

# Store the Genie Space ID
databricks secrets put --scope voc-app --key genie-space-id
```

### Step 2: Update app.yaml

Edit `app.yaml` to reference your secrets:

```yaml
env:
  - name: DATABRICKS_CLIENT_SECRET
    value: ${secrets/voc-app/client-secret}
  
  - name: GENIE_SPACE_ID
    value: ${secrets/voc-app/genie-space-id}
```

Update other values to match your environment:
- `DATABRICKS_HOST`: Your workspace URL
- `DATABRICKS_CLIENT_ID`: Your service principal ID
- `DATABRICKS_SQL_WAREHOUSE_PATH`: Your SQL warehouse HTTP path
- `LAKEBASE_INSTANCE_NAME`: Your Lakebase instance name
- `LAKEBASE_DB_NAME`: Your Lakebase database name

### Step 3: Validate Configuration

Test locally first:

```bash
# Ensure .env file has correct values
cp example.env .env
# Edit .env with your actual values

# Install dependencies
pip install -r requirements.txt

# Run locally
python dash_app.py
```

Verify:
- App starts on http://localhost:8000
- Can connect to Databricks
- Can query Unity Catalog tables
- Genie queries work
- Email generation functions

### Step 4: Deploy to Databricks Apps

```bash
# Deploy the app
databricks apps deploy

# Check deployment status
databricks apps list

# View logs (if needed)
databricks apps logs <app-name>
```

### Step 5: Verify Deployment

- [ ] App is accessible at the Databricks Apps URL
- [ ] Can log in and see properties
- [ ] Property details load correctly
- [ ] Embedded dashboard renders
- [ ] Genie queries return results
- [ ] Email generation works
- [ ] All tabs in HQ Dashboard function properly

## Troubleshooting

### App Won't Start

Check logs for common issues:
```bash
databricks apps logs voc-hotel-app
```

**Common causes:**
- Missing or incorrect environment variables
- Service principal lacks permissions
- SQL warehouse is stopped
- Lakebase instance not accessible

### Database Connection Errors

**Symptoms:** App shows placeholder data

**Solutions:**
1. Verify SQL warehouse is running
2. Check service principal permissions on Unity Catalog
3. Validate `DATABRICKS_SQL_WAREHOUSE_PATH` format
4. Test connection from Databricks notebook

### Genie Queries Not Working

**Symptoms:** Genie returns errors or empty responses

**Solutions:**
1. Verify `GENIE_SPACE_ID` is correct
2. Check service principal has Genie access
3. Ensure Genie Space is published and accessible
4. Test Genie queries in Databricks UI first

### Lakebase Connection Fails

**Symptoms:** Runbook data not loading

**Solutions:**
1. Verify `LAKEBASE_INSTANCE_NAME` and `LAKEBASE_DB_NAME` are correct
2. Check service principal has Lakebase access
3. Verify `voc.aspect_runbook_db` table exists
4. Test connection from Databricks notebook

## Monitoring

### Application Health

Monitor app health through:
- Databricks Apps dashboard
- Health check endpoint: `https://<your-app-url>/health`
- Application logs in Databricks UI

### Performance Metrics

Key metrics to monitor:
- Response time for property loading
- Genie query latency
- Database connection pool usage
- Error rates in logs

### Logs

View real-time logs:
```bash
databricks apps logs voc-hotel-app --follow
```

## Rollback

If deployment fails or issues arise:

```bash
# Roll back to previous version
databricks apps deploy --version <previous-version>

# Or delete the app and redeploy
databricks apps delete voc-hotel-app
databricks apps deploy
```

## Maintenance

### Updating the App

1. Make changes locally and test
2. Commit changes to version control
3. Deploy update: `databricks apps deploy`
4. Verify update in production

### Rotating Secrets

Periodically rotate sensitive credentials:

```bash
# Update service principal secret
databricks secrets put --scope voc-app --key client-secret

# Restart app to pick up new secret
databricks apps restart voc-hotel-app
```

## Support

For issues or questions:
1. Check Databricks Apps documentation
2. Review application logs
3. Verify all prerequisites are met
4. Contact Databricks support if needed

