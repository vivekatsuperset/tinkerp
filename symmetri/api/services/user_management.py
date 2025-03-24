import traceback

from symmetri.api.db.user_repository import UserRepository
from symmetri.api.domain.users import User
from symmetri.db.base import DbProvider
from symmetri.symmetri_logger import logger


class UserManagementService(object):

    def __init__(self, db_provider: DbProvider):
        self.user_repository = UserRepository()
        self.db_provider = db_provider

    def create_user(self, user) -> User:
        logger.info("*** UserManagementService => create_user ***")
        logger.info(user)
        connection = self.db_provider.get_default_connection()
        new_user: User | None = None
        try:
            new_user = self.user_repository.create_user(connection, user)
            connection.commit()
        except Exception as e:
            traceback.print_exc()
            connection.rollback()
        finally:
            connection.close()
        return new_user

    def get_user_by_partner_user_id(self, partner_user_id: str) -> User:
        connection = self.db_provider.get_default_connection()
        user: User | None = None
        try:
            user = self.user_repository.get_user_by_partner_user_id(
                connection=connection,
                partner_user_id=partner_user_id
            )
        except Exception as e:
            traceback.print_exc()
            connection.rollback()
        finally:
            connection.close()
        return user
