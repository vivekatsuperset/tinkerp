from symmetri.db.base import DbProvider
from symmetri.db.snowflake import SnowflakeDbProvider
from symmetri.db.postgres import PostgresProvider


def get_db_provider(name: str, database: str, schema: str) -> DbProvider:
    if name == 'postgres':
        return PostgresProvider(database, schema)
    elif name == 'snowflake':
        return SnowflakeDbProvider(database, schema)
    else:
        raise ValueError(f'Unknown database provider: {name}')
