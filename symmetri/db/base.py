from abc import ABC, abstractmethod


class Column(object):

    def __init__(self, name: str, data_type: str, nullable: bool = True, primary_key: bool = False, default_value=None):
        self.name = name
        self.data_type = data_type
        self.nullable = nullable
        self.primary_key = primary_key
        self.default_value = default_value

    def __str__(self) -> str:
        parts = [
            f"Column: {self.name}",
            f"Type: {self.data_type}",
            f"Nullable: {'Yes' if self.nullable else 'No'}",
            f"Primary Key: {'Yes' if self.primary_key else 'No'}"
        ]
        if self.default_value is not None:
            parts.append(f"Default Value: {self.default_value}")
        return " | ".join(parts)


class Table(object):

    def __init__(self, name: str, columns: list[Column]):
        self.name = name
        self.columns = columns

    def __str__(self) -> str:
        output = [f"Table: {self.name}", "\nColumns:"]
        for col in self.columns:
            output.append(f"  - {str(col)}")
        return "\n".join(output)


class DbProvider(ABC):

    def __init__(self, database: str, schema: str):
        self.database = database
        self.schema = schema

    def get_db_provider_database(self) -> str:
        return self.database

    def get_default_connection(self):
        return self.get_connection_for_schema(schema=self.schema)

    def get_db_provider_schema(self) -> str:
        return self.schema

    @abstractmethod
    def get_connection_for_schema(self, schema: str):
        raise NotImplementedError()

    @abstractmethod
    def get_table_columns(self, connection, schema: str, tables_in_filter: set[str]) -> dict[str, list[Column]]:
        raise NotImplementedError()

    def get_default_catalog(self, table_names: list[str] = None) -> list[Table]:
        connection = self.get_default_connection()
        return self.get_catalog(
            connection=connection,
            schema=self.get_db_provider_schema(),
            table_names=table_names
        )

    def get_catalog(self, connection, schema: str, table_names: list[str] = None) -> list[Table]:
        tables_in_filter = None
        if table_names is not None and len(table_names) > 0:
            tables_in_filter = set(table_names)

        table_columns = self.get_table_columns(
            connection=connection,
            schema=schema,
            tables_in_filter=tables_in_filter
        )

        tables = list[Table]()
        for table_name, columns in table_columns.items():
            tables.append(
                Table(
                    name=table_name,
                    columns=columns
                )
            )

        return tables

