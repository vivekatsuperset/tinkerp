import random
from datetime import datetime, timedelta

import numpy as np
import pandas as pd


class CRMDataGenerator:
    """Generates CRM user data."""

    def __init__(self, user_pool_manager, constants, utilities, output_dir):
        self.user_pool_manager = user_pool_manager
        self.constants = constants
        self.utilities = utilities
        self.output_dir = output_dir

    def _generate_last_login_date(self, registration_date: datetime, current_date: datetime) -> datetime:
        """Generate a last login date that's between registration date and current date.
        
        Args:
            registration_date: The user's registration date
            current_date: The current date
            
        Returns:
            datetime: A valid last login date
        """
        days_since_registration = max(0, (current_date - registration_date).days)
        if days_since_registration == 0:
            return registration_date
        return registration_date + timedelta(days=random.randint(0, days_since_registration))

    def generate_crm_data(self) -> pd.DataFrame:
        """Generate CRM_USERS table data.
        
        Returns:
            pd.DataFrame: DataFrame containing generated CRM user data
        """
        print("Generating CRM_USERS table...")

        current_date = datetime.now()

        # Generate all registration dates at once
        registration_dates = [self.utilities.generate_registration_date()
                              for _ in self.user_pool_manager.crm_users]

        # Pre-generate common random choices
        # Generate loyalty tiers with weighted distribution
        loyalty_tier_weights = self.constants.LOYALTY_TIERS
        loyalty_tiers = np.random.choice(
            list(loyalty_tier_weights.keys()),
            size=len(self.user_pool_manager.crm_users),
            p=list(loyalty_tier_weights.values())
        )
        
        # Generate genders with weighted distribution
        gender_weights = self.constants.GENDERS
        genders = np.random.choice(
            list(gender_weights.keys()),
            size=len(self.user_pool_manager.crm_users),
            p=list(gender_weights.values())
        )
        
        # Generate countries with weighted distribution
        country_weights = self.constants.COUNTRIES
        countries = np.random.choice(
            list(country_weights.keys()),
            size=len(self.user_pool_manager.crm_users),
            p=list(country_weights.values())
        )

        # Generate marketing consents with weighted distribution
        consent_weights = self.constants.MARKETING_CONSENT_WEIGHTS
        marketing_consents = np.random.choice(
            list(consent_weights.keys()),
            size=len(self.user_pool_manager.crm_users),
            p=list(consent_weights.values())
        )

        # Generate loyalty points based on tier
        # Generate beta values for all users at once
        beta_values = np.random.beta(2, 5, size=len(self.user_pool_manager.crm_users))
        
        # Create arrays for min and max values based on tiers
        min_points = np.array([self.constants.LOYALTY_POINTS_RANGES[tier]['min'] for tier in loyalty_tiers])
        max_points = np.array([self.constants.LOYALTY_POINTS_RANGES[tier]['max'] for tier in loyalty_tiers])
        
        # Calculate points for all users at once
        loyalty_points = (min_points + (max_points - min_points) * beta_values).astype(int)

        # Generate data using list comprehension
        crm_data = [
            {
                'user_email_sha256': user_hash,
                'registration_date': reg_date,
                'first_name': self.utilities.fake.first_name(),
                'last_name': self.utilities.fake.last_name(),
                'birth_date': self.utilities.generate_birth_date(),
                'gender': gender,
                'country': country,
                'city': self.utilities.fake.city(),
                'postal_code': self.utilities.fake.zipcode(),
                'marketing_consent': consent,
                'loyalty_tier': tier,
                'loyalty_points': points,
                'email_engagement_score': round(random.uniform(0, 10), 2),
                'last_login_date': self._generate_last_login_date(reg_date, current_date)
            }
            for user_hash, reg_date, gender, country, consent, tier, points
            in zip(
                self.user_pool_manager.crm_users,
                registration_dates,
                genders,
                countries,
                marketing_consents,
                loyalty_tiers,
                loyalty_points
            )
        ]
        return pd.DataFrame(crm_data)
