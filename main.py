import os

import click
from dotenv import load_dotenv

from cli import audience_planner, schema_analyzer, add_organization
from symmetri.symmetri_logger import setup_logs
from symmetri.etl.data_generator import DataGenerator
from symmetri.etl.snowflake.connection_manager import SnowflakeConnectionManager

@click.group()
def commands():
    pass


@commands.command()
@click.option(
    '--llm', '-l',
    type=str,
    help='the llm to use: (openai | anthropic)',
    required=True
)
@click.option(
    '--model', '-m',
    type=str,
    help='the model to use from the llm: (openai: [gpt-4o | gpt-4o-mini] | anthropic: [claude-3-7-sonnet-latest | claude-3-5-haiku-latest])',
    required=True
)
def audience_planner_cli(llm: str, model: str):
    audience_planner(llm=llm, model=model)


@commands.command()
@click.option(
    '--llm', '-l',
    type=str,
    help='the llm to use: (openai | anthropic)',
    required=True
)
@click.option(
    '--model', '-m',
    type=str,
    help='the model to use from the llm: (openai: [gpt-4o | gpt-4o-mini] | anthropic: [claude-3-7-sonnet-latest | claude-3-5-haiku-latest])',
    required=True
)
@click.option(
    '--snowflake_db', '-d',
    type=str,
    help='the snowflake database that contains the data for the organization',
    required=True
)
@click.option(
    '--org_code', '-o',
    type=str,
    help='the organization code in the Symmetri App',
    required=True
)
def schema_analyzer_cli(llm: str, model: str, snowflake_db: str, org_code: str):
    schema_analyzer(
        snowflake_db=snowflake_db, organization_code=org_code,
        llm=llm, model=model
    )


@commands.command()
@click.option(
    '--code', '-c',
    type=str,
    help='the organization code in the Symmetri App',
    required=True
)
@click.option(
    '--name', '-n',
    type=str,
    help='the organization name in the Symmetri App',
    required=True
)
def add_organization_cli(code: str, name: str):
    add_organization(code, name)


@commands.command()
@click.option(
    '--config_file', '-c',
    type=str,
    help='the YAML config that contains the metadata to drive the data generation process',
    required=True
)
@click.option(
    '--output_dir', '-o',
    type=str,
    help='the output directory for the generated datasets',
    required=True
)
@click.option(
    '--snowflake_db', '-d',
    type=str,
    help='the snowflake database to load the data into',
    required=True
)
def data_generator(config_file:str, output_dir:str, snowflake_db:str):
    scm = SnowflakeConnectionManager(
        snowflake_database=snowflake_db,
        snowflake_schema='SYMMETRI'
    )
    connection = scm.get_connection()
    connection.close()

    generator = DataGenerator(
        config_path=config_file, 
        output_dir=output_dir, 
        snowflake_db=snowflake_db, 
        snowflake_schema='SYMMETRI'
    )
    generator.generate_all_data()


def main():
    load_dotenv()
    setup_logs(os.getenv('SUPERSEEK_LOG_LEVEL', 'INFO'))
    commands()


if __name__ == "__main__":
    main()