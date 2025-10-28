"""
Database Service - Handles Databricks SQL connections for reading Delta tables and Lakebase OLTP
"""

import os
import uuid
from functools import lru_cache
from typing import List, Dict, Any, Optional
import pandas as pd
from databricks import sql
from databricks.sdk.core import Config
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
    """psycopg3 Connection that injects a fresh OAuth token as the password."""
    
    @classmethod
    def connect(cls, conninfo: str = "", **kwargs):
        w = WorkspaceClient()
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
        try:
            self.cfg = Config()
            self.http_path = os.getenv('DATABRICKS_SQL_WAREHOUSE_PATH')
            self._connection_available = True
        except Exception as e:
            print(f"⚠️  Warning: Failed to initialize Databricks config: {e}")
            print("📊 Will use placeholder data")
            self.cfg = None
            self.http_path = None
            self._connection_available = False
        
        # Lakebase OLTP configuration
        self.lakebase_instance_name = os.getenv('LAKEBASE_INSTANCE_NAME')
        self.lakebase_database = os.getenv('LAKEBASE_DB_NAME', 'databricks_postgres')
        self.lakebase_schema = os.getenv('LAKEBASE_SCHEMA', 'public')
        self._lakebase_pool = None
        
        if not self.http_path:
            if self._connection_available:
                print("⚠️  Warning: DATABRICKS_SQL_WAREHOUSE_PATH not set - using placeholder data")
            self._connection_available = False
    
    @lru_cache(maxsize=1)
    def get_connection(self):
        """Get or create a cached database connection"""
        if not self._connection_available or not self.cfg:
            return None
        
        try:
            return sql.connect(
                server_hostname=self.cfg.host.split("https://", 1)[-1],
                http_path=self.http_path,
                credentials_provider=lambda: self.cfg.authenticate,
            )
        except Exception as e:
            print(f"⚠️  Warning: Failed to connect to Databricks: {str(e)}")
            self._connection_available = False
            return None
    
    def query(self, sql_query: str) -> List[Dict[str, Any]]:
        """
        Execute a SQL query and return results as a list of dictionaries
        
        Args:
            sql_query: SQL query string to execute
            
        Returns:
            List of dictionaries where each dict represents a row, or None if connection failed
        """
        conn = self.get_connection()
        
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
    
    def query_to_pandas(self, sql_query: str):
        """
        Execute a SQL query and return results as a pandas DataFrame
        
        Args:
            sql_query: SQL query string to execute
            
        Returns:
            pandas DataFrame with query results
        """
        conn = self.get_connection()
        
        with conn.cursor() as cursor:
            cursor.execute(sql_query)
            return cursor.fetchall_arrow().to_pandas()
    
    # ========================================
    # Lakebase OLTP Methods
    # ========================================
    
    def _get_lakebase_pool(self):
        """Get or create a Lakebase connection pool with OAuth token rotation"""
        if not LAKEBASE_AVAILABLE:
            print("⚠️  Warning: psycopg not installed - cannot connect to Lakebase")
            return None
        
        if not self.lakebase_instance_name:
            print("⚠️  Warning: LAKEBASE_INSTANCE_NAME not set - Lakebase features unavailable")
            return None
        
        if self._lakebase_pool is not None:
            return self._lakebase_pool
        
        try:
            w = WorkspaceClient()
            user = "voc-demo" #w.current_user.me().user_name
            host = w.database.get_database_instance(name=self.lakebase_instance_name).read_write_dns
            
            self._lakebase_pool = ConnectionPool(
                conninfo=f"host={host} dbname={self.lakebase_database} user={user}",
                connection_class=RotatingTokenConnection,
                kwargs={"_instance_name": self.lakebase_instance_name},
                min_size=1,
                max_size=5,
                open=True,
            )
            
            print(f"✅ Connected to Lakebase instance: {self.lakebase_instance_name}")
            return self._lakebase_pool
            
        except Exception as e:
            print(f"⚠️  Warning: Failed to connect to Lakebase: {str(e)}")
            return None
    
    def query_lakebase(self, sql_query: str) -> Optional[List[Dict[str, Any]]]:
        """
        Execute a SQL query on Lakebase OLTP database and return results as list of dicts
        
        Args:
            sql_query: SQL query string to execute (PostgreSQL syntax)
            
        Returns:
            List of dictionaries where each dict represents a row, or None if connection failed
        """
        pool = self._get_lakebase_pool()
        
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
    
    def query_lakebase_to_pandas(self, sql_query: str) -> Optional[pd.DataFrame]:
        """
        Execute a SQL query on Lakebase OLTP database and return results as pandas DataFrame
        
        Args:
            sql_query: SQL query string to execute (PostgreSQL syntax)
            
        Returns:
            pandas DataFrame with query results, or None if connection failed
        """
        pool = self._get_lakebase_pool()
        
        if pool is None:
            return None
        
        try:
            with pool.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(sql_query)
                    
                    # Handle queries that don't return data
                    if cur.description is None:
                        return pd.DataFrame()
                    
                    columns = [d.name for d in cur.description]
                    rows = cur.fetchall()
                    
            return pd.DataFrame(rows, columns=columns)
            
        except Exception as e:
            print(f"⚠️  Warning: Lakebase query failed: {str(e)}")
            return None
    
    def close_lakebase_pool(self):
        """Close the Lakebase connection pool"""
        if self._lakebase_pool is not None:
            try:
                self._lakebase_pool.close()
                print("✅ Lakebase connection pool closed")
            except Exception as e:
                print(f"⚠️  Warning: Error closing Lakebase pool: {str(e)}")
            finally:
                self._lakebase_pool = None


# Singleton instance
database_service = DatabaseService()

