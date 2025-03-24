import copy
import os

import yaml


class ConfigLoader:

    def __init__(self, base_config_dir="./config"):
        self.base_config_dir = base_config_dir
        self.loaded_configs = {}  # Cache of loaded configs

    def load_config(self, config_path):
        """
        Load configuration from a YAML file, including any imported files.
        
        Args:
            config_path: Path to the main configuration YAML file
            
        Returns:
            dict: Complete merged configuration
        """
        # Use absolute path for config_path
        full_config_path = os.path.join(self.base_config_dir, config_path)

        # Check if we've already loaded this config
        if full_config_path in self.loaded_configs:
            return copy.deepcopy(self.loaded_configs[full_config_path])

        # Load the main config file
        with open(full_config_path, 'r') as file:
            config = yaml.safe_load(file)

        # Handle imports if present
        if 'imports' in config:
            imports = config.pop('imports')
            merged_config = {}

            # Load and merge each imported config
            for import_path in imports:
                import_full_path = os.path.join(self.base_config_dir, import_path)
                import_config = self._load_single_config(import_full_path)
                merged_config = self._deep_merge(merged_config, import_config)

            # Merge the main config (overrides imports)
            merged_config = self._deep_merge(merged_config, config)

            # Process special directives
            merged_config = self._process_special_directives(merged_config)

            # Cache the result
            self.loaded_configs[full_config_path] = copy.deepcopy(merged_config)
            return merged_config
        else:
            # No imports, just return the config
            # Cache the result
            self.loaded_configs[full_config_path] = copy.deepcopy(config)
            return config

    def _load_single_config(self, config_path):
        """Load a single config file without processing imports."""
        with open(config_path, 'r') as file:
            return yaml.safe_load(file)

    def _deep_merge(self, dict1, dict2):
        """
        Recursively merge dict2 into dict1.
        If there are overlapping keys, values from dict2 take precedence,
        except for lists which are combined.
        """
        result = copy.deepcopy(dict1)

        for key, value in dict2.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                # Recursively merge nested dictionaries
                result[key] = self._deep_merge(result[key], value)
            elif key in result and isinstance(result[key], list) and isinstance(value, list):
                # Combine lists
                result[key] = result[key] + [item for item in value if item not in result[key]]
            else:
                # Otherwise dict2 values override dict1
                result[key] = copy.deepcopy(value)

        return result

    def _process_special_directives(self, config):
        """Process special configuration directives like overrides and additions."""
        result = copy.deepcopy(config)

        # Process website event types (combine common with additional)
        if 'website' in result:
            if 'additional_event_types' in result['website'] and 'common_event_types' in result['website']:
                result['website']['event_types'] = (
                        result['website'].get('common_event_types', []) +
                        result['website'].get('additional_event_types', [])
                )
                # Remove the now-merged keys
                result['website'].pop('additional_event_types', None)
                result['website'].pop('common_event_types', None)

            # Process referrer URLs (combine common with additional)
            if 'additional_referrers' in result['website'] and 'common_referrers' in result['website']:
                # Flatten the common referrers structure
                common_refs = []
                for category in result['website'].get('common_referrers', {}).values():
                    if isinstance(category, list):
                        common_refs.extend(category)

                result['website']['referrer_urls'] = (
                        common_refs +
                        result['website'].get('additional_referrers', [])
                )
                # Remove the now-merged keys
                result['website'].pop('additional_referrers', None)
                result['website'].pop('common_referrers', None)

        # Process data provider segments (combine common with specific)
        if 'data_providers' in result:
            if 'segment_structure' in result['data_providers'] and 'common_segments' in result['data_providers']:
                result['data_providers']['segment_structure'] = self._deep_merge(
                    result['data_providers'].get('common_segments', {}),
                    result['data_providers'].get('segment_structure', {})
                )
                # Remove the now-merged key
                result['data_providers'].pop('common_segments', None)

        # Process CRM country overrides
        if 'crm' in result and 'countries_subset' in result['crm']:
            result['crm']['countries'] = result['crm']['countries_subset']
            result['crm'].pop('countries_subset', None)

        # Process sales currency overrides
        if 'sales' in result and 'currencies_override' in result['sales']:
            result['sales']['currencies'] = result['sales']['currencies_override']
            result['sales'].pop('currencies_override', None)

        return result


def load_config(config_path, base_dir="."):
    """
    Helper function to load configuration from a YAML file.
    
    Args:
        config_path: Path to the configuration YAML file
        base_dir: Base directory for config files (for resolving imports)
        
    Returns:
        dict: Complete merged configuration
    """
    loader = ConfigLoader(base_dir)
    return loader.load_config(config_path)
