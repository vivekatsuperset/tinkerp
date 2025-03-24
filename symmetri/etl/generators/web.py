import random
import uuid
from datetime import datetime, timedelta

import numpy as np
import pandas as pd


class WebsiteEventsGenerator:
    """Generates website event data."""

    def __init__(self, user_pool_manager, constants, utilities, output_dir):
        self.user_pool_manager = user_pool_manager
        self.constants = constants
        self.utilities = utilities
        self.output_dir = output_dir
        # Load URL to category mapping logic from config if available
        self.url_category_patterns = self.constants.config.get('website', {}).get('url_category_patterns', {})

    def get_page_category_from_url(self, url):
        """Determine page category from URL based on configuration."""
        # Use the URL patterns from configuration to determine category
        for pattern, category in self.url_category_patterns.items():
            if pattern in url:
                return category

        # If no pattern matches or no patterns defined, return a random category
        return random.choice(self.constants.PAGE_CATEGORIES)

    def get_event_type_weights(self, page_category):
        """Get weighted event types based on page category."""
        # Try to get weights from configuration
        event_weights = self.constants.config.get('website', {}).get(
            'event_weights', {}).get(page_category, {})

        if event_weights:
            return event_weights

        # Default weights if not in configuration
        if page_category == "Product Pages":
            return {
                'page_view': 0.3,
                'product_view': 0.25,
                'add_to_cart': 0.15,
                'click': 0.1,
                'wishlist_add': 0.1,
                'product_comparison': 0.05,
                'scroll': 0.05
            }
        elif "Checkout" in page_category or "Cart" in page_category:
            return {
                'page_view': 0.25,
                'form_submit': 0.25,
                'purchase': 0.2,
                'click': 0.15,
                'remove_from_cart': 0.1,
                'scroll': 0.05
            }
        else:
            return {
                'page_view': 0.4,
                'click': 0.25,
                'scroll': 0.15,
                'search': 0.1,
                'form_submit': 0.05,
                'login': 0.05
            }

    def generate_website_events(self):
        """Generate WEBSITE_EVENTS table data."""
        print("Generating WEBSITE_EVENTS table...")

        if not self.constants.WEBSITE_NAMES or not self.constants.PAGE_URLS:
            print("Error: Website names or page URLs not defined in configuration.")
            return pd.DataFrame()

        # Pre-compute constants and lookups
        website_name = self.constants.WEBSITE_NAMES[0] if len(self.constants.WEBSITE_NAMES) == 1 else None
        urls_by_website = {
            name: self.constants.PAGE_URLS.get(name, []) for name in self.constants.WEBSITE_NAMES
        }

        # Cache frequently used values
        device_types = self.constants.DEVICE_TYPES or ['desktop']
        browsers = self.constants.BROWSERS or ['Chrome']
        referrer_urls = self.constants.REFERRER_URLS or ['']

        # Pre-compute event type weights by category
        event_weights_by_category = {}
        for category in self.constants.PAGE_CATEGORIES:
            weights = self.get_event_type_weights(category)
            valid_types = [et for et in weights.keys() if et in self.constants.EVENT_TYPES]
            if not valid_types:
                valid_types = list(weights.keys())

            weights_list = [weights[et] for et in valid_types]
            total = sum(weights_list)
            normalized_weights = [w / total if total > 0 else 1 / len(weights_list) for w in weights_list]

            event_weights_by_category[category] = (valid_types, normalized_weights)

        website_events_data = []
        event_id = 1
        avg_events_per_user = 10
        batch_size = 10000

        # Process users in batches
        user_batches = [
            self.user_pool_manager.website_users[i:i + batch_size]
            for i in range(0, len(self.user_pool_manager.website_users), batch_size)
        ]

        for user_batch in user_batches:
            batch_events = []

            for user_hash in user_batch:
                num_events = max(1, np.random.poisson(avg_events_per_user))
                session_id = str(uuid.uuid4())

                if not website_name:  # Multiple websites case
                    primary_website = random.choice(self.constants.WEBSITE_NAMES)
                    alternate_websites = [w for w in self.constants.WEBSITE_NAMES if w != primary_website]

                for _ in range(num_events):
                    # Determine website
                    if website_name:
                        current_website = website_name
                    else:
                        current_website = primary_website if random.random() < 0.8 else random.choice(alternate_websites)

                    # Get URL for website
                    website_urls = urls_by_website[current_website]
                    if website_urls:
                        page_url = random.choice(website_urls)
                    else:
                        page_url = f"https://{current_website}/page-{random.randint(1, 100)}"

                    # Get page category and event type
                    page_category = self.get_page_category_from_url(page_url)
                    event_types, weights = event_weights_by_category.get(
                        page_category,
                        event_weights_by_category[self.constants.PAGE_CATEGORIES[0]]
                    )
                    event_type = random.choices(event_types, weights=weights, k=1)[0]

                    # Generate event timestamp
                    event_timestamp = self.utilities.generate_date_between(
                        datetime.now() - timedelta(days=90),
                        datetime.now()
                    )

                    # Handle referrer URL
                    referrer_url = random.choice(referrer_urls)
                    if not referrer_url and random.random() < 0.7 and event_id > 1:
                        website_urls = urls_by_website[current_website]
                        if len(website_urls) > 1:
                            referrer_candidates = [url for url in website_urls if url != page_url]
                            if referrer_candidates:
                                referrer_url = random.choice(referrer_candidates)

                    # Calculate time on page
                    if "Tips" in page_category or "Tutorial" in page_category or "Product" in page_category:
                        time_on_page = int(np.random.exponential(scale=120))
                    elif "Checkout" in page_category or "Cart" in page_category:
                        time_on_page = int(np.random.normal(loc=60, scale=20))
                    else:
                        time_on_page = int(np.random.exponential(scale=45))

                    batch_events.append({
                        'event_id': event_id,
                        'user_email_sha256': user_hash,
                        'event_timestamp': event_timestamp,
                        'website_name': current_website,
                        'page_url': page_url,
                        'page_category': page_category,
                        'event_type': event_type,
                        'session_id': session_id,
                        'referrer_url': referrer_url,
                        'device_type': random.choice(device_types),
                        'browser': random.choice(browsers),
                        'time_on_page': time_on_page
                    })

                    event_id += 1
                    if random.random() < 0.2:  # ~20% chance of session change
                        session_id = str(uuid.uuid4())

            website_events_data.extend(batch_events)

        return pd.DataFrame(website_events_data)
