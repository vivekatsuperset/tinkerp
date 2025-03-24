import os

from symmetri.agents.schema_analyzer.core import SchemaAnalyzer
from symmetri.api.domain.organizations import Organization
from symmetri.api.services.organization_management import OrganizationManagementService
from symmetri.db.postgres import PostgresProvider
from symmetri.db.snowflake import SnowflakeDbProvider


def schema_analyzer(snowflake_db: str, organization_code: str,
                    llm: str, model: str):
    snowflake_db_provider = SnowflakeDbProvider(
        database=snowflake_db,
        schema='SYMMETRI',
    )

    postgres_db = os.environ.get('POSTGRES_DATABASE', None)
    postgres_schema = os.environ.get('POSTGRES_SCHEMA', None)

    postgres_db_provider = PostgresProvider(
        database=postgres_db,
        schema=postgres_schema
    )

    schema_analyzer = SchemaAnalyzer(
        snowflake_provider=snowflake_db_provider,
        postgres_provider=postgres_db_provider,
        llm_name=llm, model_name=model
    )
    schema_analyzer.analyze_schema(organization_code=organization_code)


def add_organization(code: str, name: str):
    postgres_db = os.environ.get('POSTGRES_DATABASE', None)
    postgres_schema = os.environ.get('POSTGRES_SCHEMA', None)

    postgres_db_provider = PostgresProvider(
        database=postgres_db,
        schema=postgres_schema
    )

    organization_service = OrganizationManagementService(postgres_db_provider)
    organization_service.create_organization(Organization(code=code, name=name))

