import traceback

from symmetri.api.domain.users import User


class UserRepository(object):

    def __init__(self):
        pass

    def create_user(self, connection, user: User) -> User:
        db_user = self._fetch_user_by_column(
            connection=connection,
            column_name='email',
            column_value=user.email
        )
        if db_user is None:
            db_user_id = self._add_user(
                connection=connection,
                user=user
            )
            db_user = User.clone_with_id(user, db_user_id)
        return db_user

    def get_user_by_partner_user_id(self, connection, partner_user_id: str) -> User:
        return self._fetch_user_by_column(
            connection=connection,
            column_name='partner_user_id',
            column_value=partner_user_id
        )

    def _fetch_user_by_column(self, connection, column_name: str, column_value: str) -> User:
        user: User | None = None
        try:
            cursor = connection.cursor()
            sql = """
            SELECT u.id, u.name, u.email, u.domain, u.auth_partner, u.partner_user_id,
            u.is_admin, u.created_at FROM users u WHERE u.{column_name} = %s""".format(column_name=column_name)

            cursor.execute(sql, [column_value])
            row = cursor.fetchone()
            if row is not None:
                user = User.from_db_row(row)
            cursor.close()

        except Exception as e:
            traceback.print_exc()
            user = None
        return user

    def _add_user(self, connection, user: User) -> int:
        sql = """INSERT INTO users 
        (name, email, domain, auth_partner, partner_user_id, is_admin, created_at) 
        VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING ID"""
        cursor = connection.cursor()
        cursor.execute(
            sql, [
                user.name, user.email, user.domain,
                user.auth_partner, user.partner_user_id,
                user.is_admin, user.created_at
            ]
        )
        user_id = cursor.fetchone()[0]
        cursor.close()
        return user_id
