import os
from typing import Any, Dict, List

import snowflake
import snowflake.connector as snow
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization

from symmetri.db.base import DbProvider, Column


class SnowflakeDbProvider(DbProvider):

    def __init__(self, database: str, schema: str):
        super().__init__(database, schema)
        self.user = os.environ.get('SNOWFLAKE_DB_USER', None)
        self.private_key_path = os.environ.get('SNOWFLAKE_PRIVATE_KEY_PATH', None)
        self.private_key_passphrase = os.environ.get('SNOWFLAKE_PRIVATE_KEY_PASSPHRASE', None)
        self.account = os.environ.get('SNOWFLAKE_ACCOUNT', None)
        self.warehouse = os.environ.get('SNOWFLAKE_COMPUTE_WAREHOUSE', None)
        self.role = os.environ.get('SNOWFLAKE_DB_ROLE', None)
        self.private_key = self._load_private_key()

    def get_connection_for_schema(self, schema: str):
        snow.paramstyle = 'qmark'
        return snow.connect(
            user=self.user.upper(),
            private_key=self._get_private_key_pkcs8(),
            account=self.account.upper(),
            database=self.database.upper(),
            warehouse=self.warehouse.upper(),
            role=self.role.upper(),
            autocommit=False
        )
        
    def _load_private_key(self):
        """Load the private key from file and return the key object."""
        try:
            with open(self.private_key_path, 'rb') as key_file:
                p_key = serialization.load_pem_private_key(
                    key_file.read(),
                    password=self.private_key_passphrase.encode() if self.private_key_passphrase else None,
                    backend=default_backend()
                )
                return p_key
        except Exception as e:
            raise Exception(f"Failed to load private key: {str(e)}")

    def _get_private_key_pkcs8(self):
        """Convert the private key to PKCS8 format as required by Snowflake."""
        if not self.private_key:
            raise Exception("Private key not loaded")
        
        try:
            private_key_bytes = self.private_key.private_bytes(
                encoding=serialization.Encoding.DER,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            return private_key_bytes
        except Exception as e:
            raise Exception(f"Failed to convert private key to PKCS8: {str(e)}")

    def suspend_warehouse(self):
        connection = self.get_default_connection()
        try:
            cursor = connection.cursor()
            cursor.execute("ALTER WAREHOUSE %s SUSPEND IF SUSPENDED" % self.warehouse)
            cursor.close()
        except snowflake.connector.errors.ProgrammingError:
            # ignore this exception silently.
            # this exception is thrown by snowflake when the compute warehouse cannot be suspended
            # because it is not in active state
            pass
        connection.close()

    def get_table_columns(self, connection, schema: str, tables_in_filter: set[str]) -> dict[str, list[Column]]:
        cursor = connection.cursor(snow.DictCursor)
        table_columns = dict[str, list[Column]]()

        columns_sql = """SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE, IS_NULLABLE, IS_IDENTITY, COLUMN_DEFAULT
        FROM {db}.INFORMATION_SCHEMA.COLUMNS WHERE TABLE_CATALOG = ? AND TABLE_SCHEMA = ?
        """.format(db=self.database)

        records = cursor.execute(columns_sql, [self.get_db_provider_database(), schema]).fetchall()

        for record in records:
            table_name = record['TABLE_NAME']
            if tables_in_filter is None or table_name in tables_in_filter:
                column_name = record['COLUMN_NAME']
                data_type = record['DATA_TYPE']
                nullable = record['IS_NULLABLE'] is None or record['IS_NULLABLE'].lower() == 'yes'
                primary_key = record['IS_IDENTITY'] is not None and record['IS_IDENTITY'].lower() == 'yes'
                default_value = record.get('COLUMN_DEFAULT', None)
                columns = table_columns.get(table_name, None)
                if columns is None:
                    columns = list[Column]()
                    table_columns[table_name] = columns
                columns.append(Column(column_name, data_type, nullable, primary_key, default_value))
        cursor.close()

        return table_columns

    def execute_query(self, query: str, params: dict[str, Any] = None) -> list[tuple[Any, ...]]:
        """
        Execute a SQL query and return results.
        
        Args:
            query: SQL query to execute
            params: Query parameters for parameterized queries
            
        Returns:
            List of result rows
        """
        conn = self.connect()
        cursor = None
        
        try:
            cursor = conn.cursor()
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            results = cursor.fetchall()
            
            return results
            
        except Exception as e:
            raise
            
        finally:
            if cursor:
                cursor.close()
    
    def get_table_schema(self, table_name: str) -> List[Dict[str, Any]]:
        """
        Get the schema of a table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            List of column definitions
        """
        query = f"""
        DESCRIBE TABLE {table_name}
        """
        
        raw_results = self.execute_query(query)
        
        # Format results into a more usable structure
        columns = []
        for row in raw_results:
            columns.append({
                "name": row[0],
                "type": row[1],
                "nullable": row[2] == "Y",
                "default": row[4],
                "primary_key": row[5] == "Y"
            })
        
        return columns
    
    def get_table_names(self) -> list[str]:
        """
        Get all table names in the current schema.
        
        Returns:
            List of table names
        """
        query = """
        SHOW TABLES
        """
        
        raw_results = self.execute_query(query)
        
        # Extract table names from results
        return [row[1] for row in raw_results]
    
    def get_database_info(self) -> dict[str, Any]:
        """
        Get information about the database schema.
        
        Returns:
            Dictionary with database schema information
        """
        tables = self.get_table_names()
        
        schema_info = {
            "database": self.connection_params["database"],
            "schema": self.connection_params["schema"],
            "tables": {}
        }
        
        for table in tables:
            schema_info["tables"][table] = self.get_table_schema(table)
        
        return schema_info