import datetime
import json
import os

ADMIN_USERS = os.getenv('ADMIN_USERS', '').split(',')


class User(object):

    def __init__(self, name: str, email: str, domain: str,
                 auth_partner: str, partner_user_id: str, is_admin: bool,
                 created_at: datetime.datetime, user_id: int = None):
        self.name = name
        self.email = email
        self.domain = domain
        self.auth_partner = auth_partner
        self.partner_user_id = partner_user_id
        self.is_admin = is_admin
        self.user_id = user_id
        self.created_at = created_at

    def __str__(self):
        return json.dumps({
            'user_id': self.user_id,
            'name': self.name,
            'email': self.email,
            'domain': self.domain,
            'auth_partner': self.auth_partner,
            'partner_user_id': self.partner_user_id,
            'is_admin': self.is_admin
        })

    @staticmethod
    def from_google_user_data(google_user_data):
        email = google_user_data['email']
        domain = email.split('@')[-1]
        return User(
            name=google_user_data['name'],
            email=email,
            domain=domain,
            auth_partner='google',
            partner_user_id=google_user_data['sub'],
            is_admin=User.is_user_admin(email, domain),
            created_at=datetime.datetime.now(datetime.UTC)
        )

    @staticmethod
    def from_db_row(row):
        return User(
            user_id=row[0],
            name=row[1],
            email=row[2],
            domain=row[3],
            auth_partner=row[4],
            partner_user_id=row[5],
            is_admin=row[6],
            created_at=row[7]
        )

    @staticmethod
    def clone_with_id(user, db_user_id):
        return User(
            user_id=db_user_id,
            name=user.name,
            email=user.email,
            domain=user.domain,
            auth_partner=user.auth_partner,
            partner_user_id=user.partner_user_id,
            is_admin=user.is_admin,
            created_at=user.created_at
        )

    @staticmethod
    def is_user_admin(email: str, domain: str) -> bool:
        # return domain == 'superset.com' or email in ADMIN_USERS
        return email in ADMIN_USERS
