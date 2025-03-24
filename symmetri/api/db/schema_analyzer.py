import json
from typing import Any, Dict, List, Optional
from uuid import UUID

from symmetri.api.domain.schema_analyzer import TableMetadata


class SchemaAnalyzerRepository(object):

    def __init__(self):
        pass

    def get_table_summaries(self, connection, organization_id: UUID) -> List[Dict[str, Any]]:
        """
        Get a list of lightweight table metadata summaries for all tables in the organization.
        Suitable for displaying in a list/card view.
        """
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT summary_metadata FROM schema_analyzer_metadata WHERE organization_id = %s",
                (organization_id,)
            )
            return [row[0] for row in cursor.fetchall()]  # PostgreSQL automatically deserializes JSONB

    def get_table_metadata(self, connection, organization_id: UUID, table_name: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed metadata for a specific table.
        Returns None if the table metadata doesn't exist.
        """
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT metadata FROM schema_analyzer_metadata WHERE organization_id = %s AND table_name = %s",
                (organization_id, table_name)
            )
            row = cursor.fetchone()
            if row:
                return row[0]  # PostgreSQL automatically deserializes JSONB to dict
        return None

    def store_metadata(self, connection, organization_id: UUID,
                       inserts: dict[str, TableMetadata], updates: dict[str, TableMetadata]):
        """
        Store table metadata in the database, handling both inserts and updates.
        
        Args:
            connection: Database connection
            organization_id: UUID of the organization
            inserts: Dictionary of table_name -> metadata for new tables
            updates: Dictionary of table_name -> metadata for existing tables
        """
        with connection.cursor() as cursor:
            # Handle inserts
            if inserts:
                insert_sql = """
                INSERT INTO schema_analyzer_metadata (organization_id, table_name, metadata, summary_metadata)
                VALUES (%s, %s, %s, %s)
                """
                insert_values = []
                for table_name, metadata in inserts.items():
                    insert_values.append((
                        organization_id,
                        table_name,
                        json.dumps(metadata.to_json()),
                        json.dumps(metadata.to_summary_json())
                    ))
                cursor.executemany(insert_sql, insert_values)

            # Handle updates
            if updates:
                update_sql = """
                UPDATE schema_analyzer_metadata
                SET metadata = %s,
                    summary_metadata = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE organization_id = %s AND table_name = %s
                """
                update_values = []
                for table_name, metadata in updates.items():
                    update_values.append((
                        json.dumps(metadata.to_json()),
                        json.dumps(metadata.to_summary_json()),
                        organization_id,
                        table_name
                    ))
                cursor.executemany(update_sql, update_values)

    def get_tables_with_metadata(self, connection, organization_id: UUID) -> set[str]:
        """Get the set of table names that have metadata stored for the given organization."""
        tables_with_metadata = set()
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT table_name FROM schema_analyzer_metadata WHERE organization_id = %s",
                (organization_id,)
            )
            tables_with_metadata = {row[0] for row in cursor.fetchall()}
        return tables_with_metadata