import hashlib
import random
from datetime import datetime, timedelta, date

import numpy as np
import yaml
from faker import Faker


class YAMLConfigLoader:
    """Loads configuration from YAML files."""

    @staticmethod
    def load_config(config_path):
        """Load configuration from a YAML file."""
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
        return config


class Constants:
    """Holds all configuration data loaded from YAML."""

    def __init__(self, config_path):
        """Initialize constants from YAML configuration file."""
        self.config = YAMLConfigLoader.load_config(config_path)

        # User counts and percentages
        self.TOTAL_CRM_USERS = self.config.get('user_counts', {}).get('total_crm_users', 500_000)
        self.CRM_USERS_WITH_TRANSACTIONS_PERCENTAGE = self.config.get('user_counts', {}).get(
            'crm_users_with_transactions_percentage', 0.80)
        self.TOTAL_WEBSITE_EVENTS_USERS = self.config.get('user_counts', {}).get('total_website_events_users', 800_000)
        self.WEBSITE_USERS_WITH_TRANSACTIONS_PERCENTAGE = self.config.get('user_counts', {}).get(
            'website_users_with_transactions_percentage', 0.30)
        self.WEBSITE_USERS_IN_CRM_PERCENTAGE = self.config.get('user_counts', {}).get('website_users_in_crm_percentage',
                                                                                      0.50)
        self.TOTAL_DATA_PROVIDER_USERS = self.config.get('user_counts', {}).get('total_data_provider_users', 1_000_000)
        self.DATA_PROVIDER_USERS_IN_WEBSITE_PERCENTAGE = self.config.get('user_counts', {}).get(
            'data_provider_users_in_website_percentage', 0.20)
        self.DATA_PROVIDER_USERS_IN_CRM_PERCENTAGE = self.config.get('user_counts', {}).get(
            'data_provider_users_in_crm_percentage', 0.35)

        # Website-related constants
        self.WEBSITE_NAMES = self.config.get('website', {}).get('names', [])
        self.PAGE_CATEGORIES = self.config.get('website', {}).get('page_categories', [])
        self.PAGE_URLS = self.config.get('website', {}).get('page_urls', {})
        self.EVENT_TYPES = self.config.get('website', {}).get('event_types', [])
        self.DEVICE_TYPES = self.config.get('website', {}).get('device_types', [])
        self.BROWSERS = self.config.get('website', {}).get('browsers', [])
        self.REFERRER_URLS = self.config.get('website', {}).get('referrer_urls', [])
        self.URL_CATEGORY_PATTERNS = self.config.get('website', {}).get('url_category_patterns', {})
        self.EVENT_WEIGHTS = self.config.get('website', {}).get('event_weights', {})

        # Customer/CRM related constants
        self.LOYALTY_TIERS = self.config.get('crm', {}).get('loyalty_tiers', [])
        self.LOYALTY_POINTS_RANGES = self.config.get('crm', {}).get('loyalty_points_ranges', {})
        self.GENDERS = self.config.get('crm', {}).get('genders', [])
        self.COUNTRIES = self.config.get('crm', {}).get('countries', [])
        self.MARKETING_CONSENT_WEIGHTS = self.config.get('crm', {}).get('marketing_consent_weights', {})

        # Product-related constants
        self.PRODUCT_STRUCTURE = self.config.get('products', {}).get('structure', {})
        self.PRODUCT_BRANDS = self.config.get('products', {}).get('brands', {})

        # Sales-related constants
        self.PAYMENT_METHODS = self.config.get('sales', {}).get('payment_methods', [])
        self.CURRENCIES = self.config.get('sales', {}).get('currencies', [])
        self.CHANNELS = self.config.get('sales', {}).get('channels', [])
        self.STORE_IDS = self.config.get('sales', {}).get('store_ids', [])
        if not self.STORE_IDS:
            self.STORE_IDS = [f'ST{i:03d}' for i in range(1, 51)]  # Default: 50 stores

        # Data provider related constants
        self.DATA_PROVIDERS = self.config.get('data_providers', {}).get('providers', [])
        self.SEGMENT_STRUCTURE = self.config.get('data_providers', {}).get('segment_structure', {})


class Utilities:
    """Helper utility functions."""

    def __init__(self):
        self.fake = Faker()
        # Set random seeds for reproducibility
        np.random.seed(42)
        random.seed(42)
        Faker.seed(42)

    def generate_email_sha256(self, email):
        """Generate SHA256 hash for email."""
        return hashlib.sha256(email.encode()).hexdigest()

    def generate_date_between(self, start_date, end_date):
        """Generate a random date between start_date and end_date."""
        delta = end_date - start_date
        int_delta = delta.days
        random_day = random.randint(0, int_delta)
        return start_date + timedelta(days=random_day)

    def generate_registration_date(self):
        """Generate a random registration date within the last 5 years."""
        start_date = datetime.now() - timedelta(days=5 * 365)
        end_date = datetime.now()
        return self.generate_date_between(start_date, end_date)

    def generate_birth_date(self):
        """Generate a random birth date for users between 18 and 80 years old."""
        start_date = date.today() - timedelta(days=80 * 365)
        end_date = date.today() - timedelta(days=18 * 365)
        return self.generate_date_between(start_date, end_date)

    def generate_user_email_sha256_pool(self, num_users):
        """Generate a pool of unique user email SHA256 hashes."""
        email_hashes = []
        for _ in range(num_users):
            email = self.fake.email()
            email_hash = self.generate_email_sha256(email)
            email_hashes.append(email_hash)
        return email_hashes


class UserPoolManager:
    """Manages user pools and their overlaps."""

    def __init__(self, constants, utilities):
        self.constants = constants
        self.utilities = utilities
        self.crm_users = []
        self.website_users = []
        self.data_provider_users = []
        self.crm_users_with_transactions = []
        self.website_users_with_transactions = []


class UserPoolManager:
    """Manages user pools and their overlaps."""

    def __init__(self, constants, utilities):
        self.constants = constants
        self.utilities = utilities
        self.crm_users = []
        self.website_users = []
        self.data_provider_users = []
        self.crm_users_with_transactions = []
        self.website_users_with_transactions = []


class UserPoolManager:
    """Manages user pools and their overlaps."""

    def __init__(self, constants, utilities):
        self.constants = constants
        self.utilities = utilities
        self.crm_users = []
        self.website_users = []
        self.data_provider_users = []
        self.crm_users_with_transactions = []
        self.website_users_with_transactions = []

    def generate_user_pools(self):
        """Optimized generation of user pools with required overlaps."""
        print("Generating user pools...")

        # Calculate derived numbers
        CRM_USERS_WITH_TRANSACTIONS = int(
            self.constants.TOTAL_CRM_USERS * self.constants.CRM_USERS_WITH_TRANSACTIONS_PERCENTAGE)
        WEBSITE_USERS_IN_CRM = int(
            self.constants.TOTAL_WEBSITE_EVENTS_USERS * self.constants.WEBSITE_USERS_IN_CRM_PERCENTAGE)
        WEBSITE_USERS_WITH_TRANSACTIONS = int(
            self.constants.TOTAL_WEBSITE_EVENTS_USERS * self.constants.WEBSITE_USERS_WITH_TRANSACTIONS_PERCENTAGE)
        DATA_PROVIDER_USERS_IN_WEBSITE = int(
            self.constants.TOTAL_DATA_PROVIDER_USERS * self.constants.DATA_PROVIDER_USERS_IN_WEBSITE_PERCENTAGE)
        DATA_PROVIDER_USERS_IN_CRM = int(
            self.constants.TOTAL_DATA_PROVIDER_USERS * self.constants.DATA_PROVIDER_USERS_IN_CRM_PERCENTAGE)

        # Generate all user hashes at once
        TOTAL_UNIQUE_USERS = (
                self.constants.TOTAL_CRM_USERS
                + self.constants.TOTAL_WEBSITE_EVENTS_USERS
                + self.constants.TOTAL_DATA_PROVIDER_USERS
        )
        all_users_pool = np.array(self.utilities.generate_user_email_sha256_pool(TOTAL_UNIQUE_USERS))

        # Shuffle once and then partition
        np.random.shuffle(all_users_pool)

        # Partition users into pools
        local_crm_users = all_users_pool[:self.constants.TOTAL_CRM_USERS]
        local_website_users = all_users_pool[self.constants.TOTAL_CRM_USERS:
                                             self.constants.TOTAL_CRM_USERS + self.constants.TOTAL_WEBSITE_EVENTS_USERS]
        local_data_provider_users = all_users_pool[
                                    self.constants.TOTAL_CRM_USERS + self.constants.TOTAL_WEBSITE_EVENTS_USERS:
                                    self.constants.TOTAL_CRM_USERS + self.constants.TOTAL_WEBSITE_EVENTS_USERS
                                    + self.constants.TOTAL_DATA_PROVIDER_USERS]

        # Overlap CRM -> Website
        crm_indices = np.random.choice(len(local_crm_users), WEBSITE_USERS_IN_CRM, replace=False)
        local_website_users[:WEBSITE_USERS_IN_CRM] = local_crm_users[crm_indices]

        # Overlap CRM -> Data Provider
        crm_indices_for_data_provider = np.random.choice(len(local_crm_users), DATA_PROVIDER_USERS_IN_CRM,
                                                         replace=False)
        local_data_provider_users[:DATA_PROVIDER_USERS_IN_CRM] = local_crm_users[crm_indices_for_data_provider]

        # Overlap Website -> Data Provider (excluding CRM users)
        website_non_crm_indices = np.setdiff1d(np.arange(len(local_website_users)), crm_indices, assume_unique=True)
        if len(website_non_crm_indices) > 0:
            selected_indices = np.random.choice(website_non_crm_indices, DATA_PROVIDER_USERS_IN_WEBSITE, replace=False)
            local_data_provider_users[DATA_PROVIDER_USERS_IN_CRM:
                                      DATA_PROVIDER_USERS_IN_CRM + DATA_PROVIDER_USERS_IN_WEBSITE] = \
            local_website_users[
                selected_indices]

        # Users with transactions
        local_crm_users_with_transactions = np.random.choice(local_crm_users, CRM_USERS_WITH_TRANSACTIONS,
                                                             replace=False)
        local_website_users_with_transactions = np.random.choice(local_website_users, WEBSITE_USERS_WITH_TRANSACTIONS,
                                                                 replace=False)

        self.crm_users = local_crm_users.tolist()
        self.website_users = local_website_users.tolist()
        self.data_provider_users = local_data_provider_users.tolist()
        self.crm_users_with_transactions = local_crm_users_with_transactions.tolist()
        self.website_users_with_transactions = local_website_users_with_transactions.tolist()

        # Compute overlaps
        crm_set = set(self.crm_users)
        website_set = set(self.website_users)
        data_provider_set = set(self.data_provider_users)
        crm_transactions_set = set(self.crm_users_with_transactions)
        website_transactions_set = set(self.website_users_with_transactions)

        overlap_website_crm = len(website_set & crm_set)
        overlap_crm_transactions = len(crm_transactions_set & crm_set)
        overlap_website_transactions = len(website_transactions_set & website_set)
        overlap_website_data_provider = len(website_set & data_provider_set)
        overlap_crm_data_provider = len(crm_set & data_provider_set)

        print(f"Generated user pools with following counts:")
        print(f"CRM Users: {len(self.crm_users)}")
        print(f"Website Users: {len(self.website_users)}")
        print(f"Data Provider Users: {len(self.data_provider_users)}")
        print(f"CRM Users with Transactions: {len(self.crm_users_with_transactions)}")
        print(f"Website Users with Transactions: {len(self.website_users_with_transactions)}")
        print("\nOverlap counts:")
        print(f"Website + CRM: {overlap_website_crm}")
        print(f"CRM + Transactions: {overlap_crm_transactions}")
        print(f"Website + Transactions: {overlap_website_transactions}")
        print(f"Website + Data Provider Users: {overlap_website_data_provider}")
        print(f"CRM + Data Provider Users: {overlap_crm_data_provider}")

        return self
