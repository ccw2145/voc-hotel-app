"""
Database Service - Handles Databricks SQL connections for reading Delta tables and Lakebase OLTP
"""

import os
import uuid
from typing import List, Dict, Any, Optional
import pandas as pd
from databricks import sql
from databricks.sdk.core import Config, oauth_service_principal
from databricks.sdk import WorkspaceClient

# Lakebase OLTP support (optional dependency)
try:
    import psycopg
    from psycopg_pool import ConnectionPool
    LAKEBASE_AVAILABLE = True
except ImportError:
    LAKEBASE_AVAILABLE = False
    ConnectionPool = None  # Type stub for when not installed
    print("⚠️  Note: psycopg not installed - Lakebase OLTP features unavailable")


class RotatingTokenConnection(psycopg.Connection if LAKEBASE_AVAILABLE else object):
    """psycopg3 Connection that injects a fresh OAuth token as the password with service principal auth."""
    
    @classmethod
    def connect(cls, conninfo: str = "", **kwargs):
        # Extract service principal credentials from kwargs
        client_id = kwargs.pop("_sp_client_id", None)
        client_secret = kwargs.pop("_sp_client_secret", None)
        server_hostname = kwargs.pop("_server_hostname", None)
        
        # Create WorkspaceClient with service principal credentials
        if client_id and client_secret and server_hostname:
            # Add https:// prefix if not present (server_hostname is guaranteed not None here)
            host = server_hostname if server_hostname.startswith('https://') else f"https://{server_hostname}"
            w = WorkspaceClient(
                host=host,
                client_id=client_id,
                client_secret=client_secret
            )
            print(f"🔐 Lakebase: Using service principal authentication")
        else:
            # Fallback to default credentials (should not happen with proper setup)
            w = WorkspaceClient()
            print(f"⚠️  Lakebase: Using default credentials (service principal not configured)")
        
        # Generate fresh OAuth token for Lakebase connection
        kwargs["password"] = w.database.generate_database_credential(
            request_id=str(uuid.uuid4()),
            instance_names=[kwargs.pop("_instance_name")]
        ).token
        kwargs.setdefault("sslmode", "require")
        return super().connect(conninfo, **kwargs)


class DatabaseService:
    """Singleton service for Databricks SQL and Lakebase OLTP connections"""
    
    def __init__(self):
        # Unity Catalog / SQL Warehouse configuration
        self.server_hostname = os.getenv('DATABRICKS_SERVER_HOSTNAME')
        self.http_path = os.getenv('DATABRICKS_HTTP_PATH') or os.getenv('DATABRICKS_SQL_WAREHOUSE_PATH')
        
        # Check if we have the minimum required configuration
        if self.server_hostname and self.http_path:
            self._connection_available = True
            print(f"✅ Database service initialized for {self.server_hostname}")
        else:
            print("⚠️  Warning: DATABRICKS_SERVER_HOSTNAME or DATABRICKS_HTTP_PATH not set")
            print("📊 Will use placeholder data")
            self._connection_available = False
        
        # Lakebase OLTP configuration
        self.lakebase_instance_name = os.getenv('LAKEBASE_INSTANCE_NAME')
        self.lakebase_database = os.getenv('LAKEBASE_DB_NAME', 'databricks_postgres')
    
    def _get_sp_credentials(self, role: str = 'hq', property: str = None) -> tuple:
        """
        Get service principal credentials based on role and property
        
        Args:
            role: 'hq' or 'pm'
            property: 'austin-tx' or 'boston-ma' (only for PM role)
        
        Returns:
            Tuple of (client_id, client_secret)
        """

        if role == 'hq':
            client_id = os.getenv("HQ_SP_CLIENT_ID",None)
            client_secret = os.getenv("HQ_SP_CLIENT_SECRET",None)
            # client_id = os.getenv("DATABRICKS_CLIENT_ID")
            # client_secret = os.getenv("DATABRICKS_CLIENT_SECRET")
            print(f"🔐 Using HQ/App service principal")
        elif role == 'pm':
            if property == 'boston-ma':
                client_id = os.getenv("BOSTON_SP_CLIENT_ID")
                client_secret = os.getenv("BOSTON_SP_CLIENT_SECRET")
                print(f"🔐 Using Boston PM service principal")
            elif property == 'austin-tx':
                client_id = os.getenv("AUSTIN_SP_CLIENT_ID")
                client_secret = os.getenv("AUSTIN_SP_CLIENT_SECRET")
                print(f"🔐 Using Austin PM service principal")
            else:
                # Default to HQ if property not specified
                client_id = os.getenv("DATABRICKS_CLIENT_ID")
                client_secret = os.getenv("DATABRICKS_CLIENT_SECRET")
                print(f"🔐 Using HQ service principal (PM property not specified)")
        print(f"🔐 Client ID: {client_id}")
        return (client_id, client_secret)
    
    def _credential_provider(self, role: str = 'hq', property: str = None):
        """Create OAuth service principal credential provider"""
        client_id, client_secret = self._get_sp_credentials(role, property)
        
        if not client_id or not client_secret:
            print(f"⚠️  Warning: Service principal credentials not found for role={role}, property={property}")
            cfg=Config()
            print(f"🔐 Using PAT authentication")
            return cfg.authenticate
        
        config = Config(
            host=f"https://{self.server_hostname}",
            client_id=client_id,
            client_secret=client_secret
        )
        return oauth_service_principal(config)
    
    def get_connection(self, role: str = 'hq', property: str = None):
        """
        Get database connection with role-specific service principal
        
        Args:
            role: 'hq' or 'pm'
            property: property ID (for PM role)
        
        Returns:
            SQL connection or None if connection fails
        """
        if not self._connection_available:
            return None
        
        try:
            print(f'🔗 Connecting to Databricks ({role}): {self.server_hostname}')
            return sql.connect(
                server_hostname=self.server_hostname,
                http_path=self.http_path,
                credentials_provider=lambda: self._credential_provider(role, property)
            )
        except Exception as e:
            print(f"⚠️  Warning: Failed to connect to Databricks with {role} SP: {str(e)}")
            return None
    
    def query(self, sql_query: str, role: str = 'hq', property: str = None) -> List[Dict[str, Any]]:
        """
        Execute a SQL query and return results as a list of dictionaries
        
        Args:
            sql_query: SQL query string to execute
            role: 'hq' or 'pm' - determines which service principal to use
            property: property ID (for PM role) - e.g. 'austin-tx' or 'boston-ma'
            
        Returns:
            List of dictionaries where each dict represents a row, or None if connection failed
        """
        conn = self.get_connection(role=role, property=property)
        
        if conn is None:
            return None
        
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql_query)
                
                # Get column names
                columns = [desc[0] for desc in cursor.description]
                
                # Fetch all rows and convert to list of dicts
                rows = cursor.fetchall()
                
                # Convert to list of dictionaries
                return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            print(f"⚠️  Warning: Database query failed: {str(e)}")
            return None
    
    # ========================================
    # Lakebase OLTP Methods
    # ========================================
    
    def _get_lakebase_pool(self, role: str = 'hq', property: str = None):
        """Get or create a Lakebase connection pool with OAuth token rotation and service principal auth"""
        if not LAKEBASE_AVAILABLE:
            print("⚠️  Warning: psycopg not installed - cannot connect to Lakebase")
            return None
        
        if not self.lakebase_instance_name:
            print("⚠️  Warning: LAKEBASE_INSTANCE_NAME not set - Lakebase features unavailable")
            return None
        
        if not self.server_hostname:
            print("⚠️  Warning: DATABRICKS_SERVER_HOSTNAME not set - cannot connect to Lakebase")
            return None
        
        # Note: We create a new pool with service principal credentials
        # In production, you might want to cache pools by (role, property) combination
        
        try:
            # Get service principal credentials for this role/property
            client_id, client_secret = self._get_sp_credentials(role, property)
            
            # Create WorkspaceClient with service principal to get instance details
            # Add https:// prefix if not present
            host = self.server_hostname if self.server_hostname.startswith('https://') else f"https://{self.server_hostname}"
            w = WorkspaceClient(
                host=host,
                client_id=client_id,
                client_secret=client_secret
            )
            
            user = "voc-demo"  # Database user
            host = w.database.get_database_instance(name=self.lakebase_instance_name).read_write_dns
            
            pool = ConnectionPool(
                conninfo=f"host={host} dbname={self.lakebase_database} user={user}",
                connection_class=RotatingTokenConnection,
                kwargs={
                    "_instance_name": self.lakebase_instance_name,
                    "_sp_client_id": client_id,
                    "_sp_client_secret": client_secret,
                    "_server_hostname": self.server_hostname
                },
                min_size=1,
                max_size=5,
                open=True,
            )
            
            print(f"✅ Connected to Lakebase instance: {self.lakebase_instance_name} (role={role}, property={property})")
            return pool
            
        except Exception as e:
            print(f"⚠️  Warning: Failed to connect to Lakebase: {str(e)}")
            return None
    
    def query_lakebase(self, sql_query: str, role: str = 'hq', property: str = None) -> Optional[List[Dict[str, Any]]]:
        """
        Execute a SQL query on Lakebase OLTP database and return results as list of dicts
        
        Args:
            sql_query: SQL query string to execute (PostgreSQL syntax)
            role: 'hq' or 'pm' for service principal selection
            property: property identifier (e.g., 'boston-ma', 'austin-tx') for PM role
            
        Returns:
            List of dictionaries where each dict represents a row, or None if connection failed
        """
        pool = self._get_lakebase_pool(role=role, property=property)
        
        if pool is None:
            return None
        
        try:
            with pool.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql_query)
                    
                    # Handle queries that don't return data (INSERT, UPDATE, DELETE)
                    if cur.description is None:
                        return []
                    
                    # Get column names
                    columns = [d.name for d in cur.description]
                    
                    # Fetch all rows
                    rows = cur.fetchall()
                    
                    # Convert to list of dictionaries
                    return [dict(zip(columns, row)) for row in rows]
                    
        except Exception as e:
            print(f"⚠️  Warning: Lakebase query failed: {str(e)}")
            return None
        finally:
            # Properly close the pool to avoid thread cleanup issues
            try:
                pool.close()
            except Exception as e:
                # Suppress cleanup errors in Databricks Apps environment
                pass


# Singleton instance
database_service = DatabaseService()

