import random

import pandas as pd


class DataProviderGenerator:
    """Generates data provider and segment data."""

    def __init__(self, user_pool_manager, constants, utilities, output_dir):
        self.user_pool_manager = user_pool_manager
        self.constants = constants
        self.utilities = utilities
        self.output_dir = output_dir

    def generate_data_providers(self):
        """Generate DATA_PROVIDERS table."""
        print("Generating DATA_PROVIDERS table...")

        if not self.constants.DATA_PROVIDERS:
            # Fallback if no data providers defined
            self.constants.DATA_PROVIDERS = [
                {'id': 1, 'name': 'Provider 1'},
                {'id': 2, 'name': 'Provider 2'},
                {'id': 3, 'name': 'Provider 3'}
            ]

        return pd.DataFrame(self.constants.DATA_PROVIDERS)

    def generate_data_provider_segments(self):
        """Generate DATA_PROVIDER_SEGMENTS table."""
        print("Generating DATA_PROVIDER_SEGMENTS table...")

        data_provider_segments = []
        segment_id = 1

        if not self.constants.SEGMENT_STRUCTURE:
            # Fallback if no segment structure defined
            self.constants.SEGMENT_STRUCTURE = {
                'Generic': {
                    'Type1': ['Value1', 'Value2', 'Value3'],
                    'Type2': ['ValueA', 'ValueB', 'ValueC']
                }
            }

        # Get the provider IDs
        provider_ids = [p.get('id', i + 1) for i, p in enumerate(self.constants.DATA_PROVIDERS)]

        for provider_id in provider_ids:
            # Each provider offers multiple segment categories
            for segment_category, segment_types in self.constants.SEGMENT_STRUCTURE.items():
                # Generate segments for each type within this category
                for segment_type, segment_names in segment_types.items():
                    # Add all segment names for this type
                    for segment_name in segment_names:
                        data_provider_segments.append({
                            'id': segment_id,
                            'data_provider_id': provider_id,
                            'segment_category': segment_category,
                            'segment_type': segment_type,
                            'segment_name': segment_name
                        })
                        segment_id += 1

        return pd.DataFrame(data_provider_segments)

    def generate_data_provider_user_segment_map(self, data_provider_segments):
        """Generate DATA_PROVIDER_USER_SEGMENT_MAP table."""
        print("Generating DATA_PROVIDER_USER_SEGMENT_MAP table...")

        data_provider_segments_df = pd.DataFrame(data_provider_segments)
        data_provider_user_segment_map_data = []

        # Pre-process segments data into efficient dictionaries
        provider_segments = {}
        provider_segments_by_category = {}

        # Convert DataFrame to dictionary for faster lookups
        segments_dict = data_provider_segments_df.to_dict('records')

        # Build provider and category mappings in one pass
        for segment in segments_dict:
            provider_id = segment['data_provider_id']
            category = segment['segment_category']
            segment_id = segment['id']

            # Initialize provider segments
            if provider_id not in provider_segments:
                provider_segments[provider_id] = []
            provider_segments[provider_id].append(segment_id)

            # Initialize provider category segments
            if provider_id not in provider_segments_by_category:
                provider_segments_by_category[provider_id] = {}
            if category not in provider_segments_by_category[provider_id]:
                provider_segments_by_category[provider_id][category] = []
            provider_segments_by_category[provider_id][category].append(segment_id)

        # Set of categories that should only have one selection
        single_selection_categories = {'Demographics', 'Age', 'Gender', 'Income'}

        # Process users in batches for memory efficiency
        batch_size = 10000
        user_batches = [
            self.user_pool_manager.data_provider_users[i:i + batch_size]
            for i in range(0, len(self.user_pool_manager.data_provider_users), batch_size)
        ]

        provider_ids = list(provider_segments.keys())

        for user_batch in user_batches:
            for user_hash in user_batch:
                # Determine which providers have data for this user
                num_providers = random.randint(1, len(provider_segments))
                user_providers = random.sample(provider_ids, min(num_providers, len(provider_ids)))

                for provider_id in user_providers:
                    provider_categories = provider_segments_by_category.get(provider_id, {})
                    selected_segments = []

                    # Process each category for this provider
                    for category, segment_ids in provider_categories.items():
                        if not segment_ids:
                            continue

                        max_selections = 1 if category in single_selection_categories else 2
                        num_selections = random.randint(0, max_selections)

                        if num_selections > 0:
                            selected = random.sample(segment_ids, min(num_selections, len(segment_ids)))
                            selected_segments.extend(selected)

                    # Batch append all segments for this user-provider combination
                    data_provider_user_segment_map_data.extend([
                        {
                            'data_provider_id': provider_id,
                            'data_provider_segment_id': segment_id,
                            'user_email_sha256': user_hash
                        }
                        for segment_id in selected_segments
                    ])

        return pd.DataFrame(data_provider_user_segment_map_data)
