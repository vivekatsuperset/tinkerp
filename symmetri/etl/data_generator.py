import os
import pandas as pd

import snowflake.connector as snow
from symmetri.etl.generators.common import Constants, Utilities, UserPoolManager
from symmetri.etl.generators.crm import CRMDataGenerator
from symmetri.etl.generators.data_providers import DataProviderGenerator
from symmetri.etl.generators.transactions import SalesDataGenerator
from symmetri.etl.generators.web import WebsiteEventsGenerator
from symmetri.etl.snowflake.connection_manager import SnowflakeConnectionManager


class DataGenerator:
    """Main data generator class that orchestrates the entire process."""

    def __init__(self, config_path: str, output_dir: str, snowflake_db: str, snowflake_schema: str):
        """Initialize the data generator with config path and output directory."""
        self.config_path = config_path
        self.output_dir = output_dir
        self.snowflake_db = snowflake_db
        self.snowflake_schema = snowflake_schema
        os.makedirs(output_dir, exist_ok=True)

        # Initialize components
        self.constants = Constants(config_path)
        self.utilities = Utilities()
        self.user_manager = UserPoolManager(self.constants, self.utilities)
        self.snowflake_manager = SnowflakeConnectionManager(
            snowflake_database=self.snowflake_db,
            snowflake_schema=self.snowflake_schema
        )

    def _save_dataset(self, dataset_df, csv_file, table_name):
        output_path = f"{self.output_dir}/{csv_file}.gz"
        dataset_df.to_csv(output_path, index=False, compression='gzip')
        self.snowflake_manager.write_df_to_table(
            df=dataset_df, 
            table_name=table_name
        )

        print(f"{self.snowflake_schema}.{table_name} table generated with {len(dataset_df)} rows")
        
    def generate_all_data(self):
        print(f"Starting data generation using configuration from {self.config_path}")
        print(f"Output will be saved to {self.output_dir}\n")

        # Initialize user pools
        self.user_manager.generate_user_pools()

        # Generate tables
        crm_generator = CRMDataGenerator(self.user_manager, self.constants, self.utilities, self.output_dir)
        crm_users = crm_generator.generate_crm_data()
        self._save_dataset(
            dataset_df=crm_users, csv_file="crm_users", 
            table_name="CRM_USERS"
        )

        sales_generator = SalesDataGenerator(self.user_manager, self.constants, self.utilities, self.output_dir)
        sales_transactions, sales_line_items = sales_generator.generate_sales_data()
        self._save_dataset(
            dataset_df=sales_transactions, csv_file="sales_transactions", 
            table_name="SALES_TRANSACTIONS"
        )
        self._save_dataset(
            dataset_df=sales_line_items, csv_file="sales_line_items", 
            table_name="SALES_LINE_ITEMS"
        )

        website_generator = WebsiteEventsGenerator(self.user_manager, self.constants, self.utilities, self.output_dir)
        website_events = website_generator.generate_website_events()
        self._save_dataset(
            dataset_df=website_events, csv_file="website_events", 
            table_name="WEBSITE_EVENTS"
        )

        data_provider_generator = DataProviderGenerator(self.user_manager, self.constants, 
                                                        self.utilities, self.output_dir)
        data_providers = data_provider_generator.generate_data_providers()
        data_provider_segments = data_provider_generator.generate_data_provider_segments()
        data_provider_user_segment_map = data_provider_generator.generate_data_provider_user_segment_map(
            data_provider_segments
        )

        self._save_dataset(
            dataset_df=data_providers, csv_file="data_providers", 
            table_name="DATA_PROVIDERS"
        )
        self._save_dataset(
            dataset_df=data_provider_segments, csv_file="data_provider_segments", 
            table_name="DATA_PROVIDER_SEGMENTS"
        )
        self._save_dataset(
            dataset_df=data_provider_user_segment_map, csv_file="data_provider_user_segment_map", 
            table_name="DATA_PROVIDER_USER_SEGMENT_MAP"
        )

        print(f"\nData generation complete! All files saved to {self.output_dir}/ and stored in Snowflake")
