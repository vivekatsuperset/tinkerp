import random
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Dict, Tuple

import numpy as np
import pandas as pd


class SalesDataGenerator:
    """Generates sales transaction data."""

    def __init__(self, user_pool_manager, constants, utilities, output_dir):
        self.user_pool_manager = user_pool_manager
        self.constants = constants
        self.utilities = utilities
        self.output_dir = output_dir

        # Pre-compute frequently used values
        self._product_structure_keys = list(
            self.constants.PRODUCT_STRUCTURE.keys()) if self.constants.PRODUCT_STRUCTURE else []
        self._brand_keys = list(self.constants.PRODUCT_BRANDS.keys()) if self.constants.PRODUCT_BRANDS else []
        self._store_ids = np.array(self.constants.STORE_IDS)
        self._channels = np.array(self.constants.CHANNELS)
        self._currencies = np.array(self.constants.CURRENCIES)
        self._payment_methods = np.array(self.constants.PAYMENT_METHODS)

    @lru_cache(maxsize=1000)
    def generate_product_details(self) -> Dict[str, str]:
        """Generate realistic product details based on configuration with caching."""
        if not self.constants.PRODUCT_STRUCTURE:
            return {
                'product_category': 'Generic',
                'product_type': 'Product',
                'product_brand': 'Brand',
                'product_name': f"Generic Product {random.randint(1, 100)}"
            }

        # Select random category and subcategory using pre-computed keys
        category_key = random.choice(self._product_structure_keys)
        subcategory_keys = list(self.constants.PRODUCT_STRUCTURE[category_key].keys())
        subcategory_key = random.choice(subcategory_keys)
        product_type = random.choice(self.constants.PRODUCT_STRUCTURE[category_key][subcategory_key])

        # Select appropriate brand if available
        if self._brand_keys:
            brand_key = random.choice(self._brand_keys)
            if self.constants.PRODUCT_BRANDS[brand_key]:
                brand_line = random.choice(self.constants.PRODUCT_BRANDS[brand_key])
                product_name = f"{brand_key} {brand_line} {product_type}"
            else:
                product_name = f"{brand_key} {product_type}"
        else:
            brand_key = 'Generic Brand'
            product_name = f"{brand_key} {product_type}"

        return {
            'product_category': category_key,
            'product_sub_category': subcategory_key,
            'product_type': product_type,
            'product_brand': brand_key,
            'product_name': product_name
        }

    def generate_sales_data(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Generate SALES_TRANSACTIONS and SALES_LINE_ITEMS table data using vectorized operations."""
        print("Generating SALES_TRANSACTIONS and SALES_LINE_ITEMS tables...")

        # Combine users with transactions efficiently using set operations
        all_users_with_transactions = list(
            set(self.user_pool_manager.crm_users_with_transactions) |
            set(self.user_pool_manager.website_users_with_transactions)
        )

        # Calculate transactions per user using vectorized operations
        avg_transactions_per_user = 3
        num_users = len(all_users_with_transactions)
        transactions_per_user = np.maximum(1, np.random.poisson(avg_transactions_per_user, size=num_users))
        total_transactions = int(np.sum(transactions_per_user))

        # Generate base transaction data
        transaction_ids = np.arange(1, total_transactions + 1)
        user_indices = np.repeat(np.arange(num_users), transactions_per_user)

        # Generate timestamps vectorized
        date_range = (datetime.now() - timedelta(days=365), datetime.now())
        timestamps = [
            self.utilities.generate_date_between(*date_range)
            for _ in range(total_transactions)
        ]

        # Generate transaction attributes vectorized
        store_ids = np.random.choice(self._store_ids, total_transactions)
        channels = np.random.choice(self._channels, total_transactions)
        currencies = np.random.choice(self._currencies, total_transactions)
        payment_methods = np.random.choice(self._payment_methods, total_transactions)

        # Prepare line items data
        line_items_data = []
        transaction_totals = np.zeros(total_transactions)
        current_line_item_id = 1

        for idx in range(total_transactions):
            num_items = random.randint(1, 5)

            # Generate line items in bulk for this transaction
            quantities = np.random.randint(1, 4, size=num_items)
            unit_prices = np.random.uniform(10, 500, size=num_items).round(2)
            discount_mask = np.random.random(num_items) < 0.4
            discount_amounts = np.where(
                discount_mask,
                unit_prices * np.random.uniform(0, 0.3, size=num_items),
                0
            ).round(2)

            total_line_amounts = ((unit_prices - discount_amounts / quantities) * quantities).round(2)
            transaction_totals[idx] = np.sum(total_line_amounts)

            # Generate product details for each line item
            for item_idx in range(num_items):
                product_details = self.generate_product_details()
                line_items_data.append({
                    'line_item_id': current_line_item_id + item_idx,
                    'transaction_id': transaction_ids[idx],
                    'product_id': random.randint(1, 1000),
                    **product_details,
                    'quantity': quantities[item_idx],
                    'unit_price': unit_prices[item_idx],
                    'discount_amount': discount_amounts[item_idx],
                    'total_line_amount': total_line_amounts[item_idx]
                })

            current_line_item_id += num_items

        # Create transactions DataFrame
        transactions_df = pd.DataFrame({
            'transaction_id': transaction_ids,
            'user_email_sha256': [all_users_with_transactions[i] for i in user_indices],
            'transaction_timestamp': timestamps,
            'total_amount': transaction_totals.round(2),
            'currency': currencies,
            'payment_method': payment_methods,
            'store_id': store_ids,
            'channel': channels
        })

        # Create line items DataFrame
        line_items_df = pd.DataFrame(line_items_data)

        return transactions_df, line_items_df
