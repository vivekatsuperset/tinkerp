from typing import Dict, List, Any

from symmetri.agents.schema_analyzer.llm import SchemaAnalyzerLLM
from symmetri.api.domain.schema_analyzer import TableMetadata
from symmetri.api.services.organization_management import OrganizationManagementService
from symmetri.api.services.schema_analyzer import SchemaAnalyzerService
from symmetri.db.base import Table, Column
from symmetri.db.postgres import PostgresProvider
from symmetri.db.snowflake import SnowflakeDbProvider


class SchemaAnalyzer:

    def __init__(self, snowflake_provider: SnowflakeDbProvider, postgres_provider: PostgresProvider, 
                 llm_name: str, model_name: str):
        self.snowflake = snowflake_provider
        self.postgres = postgres_provider
        self.llm = SchemaAnalyzerLLM(llm_name, model_name)

    def analyze_schema(self, organization_code: str) -> dict[str, TableMetadata]:
        schema_metadata = dict[str, TableMetadata]()

        tables: list[Table] = self.snowflake.get_default_catalog()

        for table in tables:
            table_metadata = self.llm.analyze_table(table.name, table.columns)

            # Add sample values to metadata after LLM analysis
            # sample_values = self._get_sample_values(table.name, table.columns)
            # table_metadata = self._enrich_metadata_with_samples(table_metadata, sample_values)

            schema_metadata[table.name] = table_metadata

        organization_management_service = OrganizationManagementService(self.postgres)
        organization = organization_management_service.get_organization_by_code(organization_code)

        schema_analyzer_service = SchemaAnalyzerService(self.postgres)
        schema_analyzer_service.store_table_metadata(organization.organization_id, schema_metadata)

        return schema_metadata

    def _enrich_metadata_with_samples(self, metadata: TableMetadata,
                                      sample_values: Dict[str, List[Any]]) -> TableMetadata:
        """Add sample values to metadata after LLM analysis."""
        for column in metadata.columns:
            if column.name in sample_values:
                column.sample_values = sample_values[column.name]
        return metadata

    def _get_sample_values(self, table_name: str, columns: list[Column],
                           max_samples: int = 5) -> Dict[str, List[Any]]:
        sample_values = {}

        # Identify key columns (excluding large text fields, timestamps, etc.)
        key_columns = [
            col.name for col in columns
            if col.data_type.upper() in ("VARCHAR", "CHAR", "STRING", "NUMBER", "INTEGER", "BOOLEAN")
        ]

        if not key_columns:
            return sample_values

        # Build query to get sample values
        columns_str = ", ".join(key_columns)
        query = f"""
        SELECT DISTINCT {columns_str}
        FROM {table_name}
        WHERE {" AND ".join(f"{col} IS NOT NULL" for col in key_columns)}
        LIMIT {max_samples}
        """

        try:
            results = self.snowflake.execute_query(query)
            for i, col in enumerate(key_columns):
                sample_values[col] = [row[i] for row in results]
        except Exception:
            pass

        return sample_values
