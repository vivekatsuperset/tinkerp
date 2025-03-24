import traceback
from typing import Any, Dict, List, Optional
from uuid import UUID

from symmetri.api.db.schema_analyzer import SchemaAnalyzerRepository
from symmetri.api.domain.schema_analyzer import TableMetadata
from symmetri.db.base import DbProvider


class SchemaAnalyzerService(object):

    def __init__(self, db_provider: DbProvider):
        self.repository = SchemaAnalyzerRepository()
        self.db_provider = db_provider

    def store_table_metadata(self, organization_id: UUID, table_metadata: dict[str, TableMetadata]) -> bool:
        """
        Store metadata for multiple tables, handling both inserts and updates.
        
        Args:
            organization_id: UUID of the organization
            table_metadata: Dictionary mapping table names to their metadata
            
        Returns:
            bool: True if operation was successful, False otherwise
        """
        connection = self.db_provider.get_default_connection()
        try:
            tables_with_metadata = self.repository.get_tables_with_metadata(connection, organization_id)
            updates = dict[str, TableMetadata]()
            inserts = dict[str, TableMetadata]()
            for table in table_metadata.keys():
                if table in tables_with_metadata:
                    updates[table] = table_metadata[table]
                else:
                    inserts[table] = table_metadata[table]
            self.repository.store_metadata(connection, organization_id, inserts, updates)
            connection.commit()
            return True
        except Exception as e:
            traceback.print_exc()
            connection.rollback()
            return False
        finally:
            connection.close()

    def get_table_summaries(self, organization_id: UUID) -> List[Dict[str, Any]]:
        """
        Get lightweight summaries of all tables for an organization.
        
        Args:
            organization_id: UUID of the organization
            
        Returns:
            List of table summaries suitable for list/card view
        """
        connection = self.db_provider.get_default_connection()
        try:
            return self.repository.get_table_summaries(connection, organization_id)
        except Exception as e:
            traceback.print_exc()
            return []
        finally:
            connection.close()

    def get_table_metadata(self, organization_id: UUID, table_name: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed metadata for a specific table.
        
        Args:
            organization_id: UUID of the organization
            table_name: Name of the table to get metadata for
            
        Returns:
            Full table metadata if found, None otherwise
        """
        connection = self.db_provider.get_default_connection()
        try:
            return self.repository.get_table_metadata(connection, organization_id, table_name)
        except Exception as e:
            traceback.print_exc()
            return None
        finally:
            connection.close()
