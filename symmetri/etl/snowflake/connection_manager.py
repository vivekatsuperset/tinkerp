import os
import pandas as pd

import snowflake.connector as snow
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from snowflake.connector.pandas_tools import write_pandas


class SnowflakeConnectionManager(object):

    def __init__(self, snowflake_database: str, snowflake_schema: str):
        self.user = os.environ.get('SNOWFLAKE_DB_USER', None)
        self.private_key_path = os.environ.get('SNOWFLAKE_PRIVATE_KEY_PATH', None)
        self.private_key_passphrase = os.environ.get('SNOWFLAKE_PRIVATE_KEY_PASSPHRASE', None)
        self.account = os.environ.get('SNOWFLAKE_ACCOUNT', None)
        self.warehouse = os.environ.get('SNOWFLAKE_COMPUTE_WAREHOUSE', None)
        self.role = os.environ.get('SNOWFLAKE_DB_ROLE', None)
        self.database = snowflake_database
        self.schema = snowflake_schema
        self.private_key = self._load_private_key()
        self.current_tables = set()
        self._load_current_tables()

    def get_connection(self):
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
        
    def _load_current_tables(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute(f"""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_SCHEMA = '{self.schema.upper()}' 
        """)
        rows = cursor.fetchall()
        for row in rows:
            self.current_tables.add(row[0])
        cursor.close()

    def write_df_to_table(self, df: pd.DataFrame, table_name: str, chunk_size: int = 1000000):
        """Store a pandas DataFrame in Snowflake.
        
        Args:
            df: DataFrame to write
            table_name: Target table name
            chunk_size: Number of rows to process in each chunk (default: 100,000)
        """
        # Reset index to ensure it's in the standard format
        df = df.reset_index(drop=True)
        
        conn = self.get_connection()
        try:
            table_exists = table_name in self.current_tables
            
            if table_exists:
                cursor = conn.cursor()
                cursor.execute(f"TRUNCATE TABLE {self.database}.{self.schema}.{table_name}")
                cursor.close()

            total_rows = len(df)
            chunks = range(0, total_rows, chunk_size)
            
            for i, chunk_start in enumerate(chunks):
                chunk_end = min(chunk_start + chunk_size, total_rows)
                df_chunk = df.iloc[chunk_start:chunk_end]
                
                write_pandas(
                    conn,
                    df_chunk,
                    table_name,
                    database=self.database,
                    schema=self.schema,
                    quote_identifiers=False,
                    auto_create_table=False
                )
                
                print(f"Chunk {i+1}/{len(chunks)}: Successfully stored rows {chunk_start+1}-{chunk_end} in {self.schema}.{table_name}")

            conn.commit()
            print(f"Completed: Successfully stored {total_rows} total rows in {self.schema}.{table_name}")
        finally:
            conn.close()

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

