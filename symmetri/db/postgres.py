import os

import psycopg

from symmetri.db.base import DbProvider, Column


class PostgresProvider(DbProvider):

    def __init__(self, database: str, schema: str):
        super().__init__(database, schema)
        self.db_user = os.environ.get('POSTGRES_DB_USER', None)
        self.db_password = os.environ.get('POSTGRES_DB_PASSWORD', None)
        self.db_host = os.environ.get('POSTGRES_DB_HOST', None).lower()
        self.db_port = int(os.environ.get('POSTGRES_DB_PORT', 0))

    def get_connection_for_schema(self, schema: str):
        connection = psycopg.connect(
            user=self.db_user,
            password=self.db_password,
            host=self.db_host,
            port=self.db_port,
            dbname=self.database,
            options=f'-c search_path={schema}'
        )
        connection.set_autocommit(True)
        return connection

    def get_table_columns(self, connection, schema: str, tables_in_filter: set[str]) -> dict[str, list[Column]]:
        table_columns = dict[str, list[Column]]()

        cursor = connection.cursor()
        rows = cursor.execute(
            """SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE 
            FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_CATALOG = %s AND TABLE_SCHEMA = %s""",
            [self.get_db_provider_database(), schema]
        ).fetchall()

        for record in rows:
            table_name = record[0]
            if tables_in_filter is None or table_name in tables_in_filter:
                column_name = record[1]
                data_type = record[2]
                columns = table_columns.get(table_name, None)
                if columns is None:
                    columns = list[Column]()
                    table_columns[table_name] = columns
                columns.append(Column(column_name, data_type))
        cursor.close()

        return table_columns
