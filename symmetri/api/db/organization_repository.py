import traceback
from datetime import datetime, UTC
from uuid import UUID

from symmetri.api.domain.organizations import Organization


class OrganizationRepository(object):

    def __init__(self):
        pass

    def create_organization(self, connection, organization: Organization) -> Organization:
        db_org = self._fetch_organization_by_column(
            connection=connection,
            column_name='code',
            column_value=organization.code
        )
        if db_org is None:
            now = datetime.now(UTC)
            organization.created_at = now
            organization.updated_at = now
            db_org_id = self._add_organization(
                connection=connection,
                organization=organization
            )
            db_org = Organization.clone_with_id(organization, db_org_id)
        return db_org

    def get_organization_by_id(self, connection, organization_id: UUID) -> Organization:
        return self._fetch_organization_by_column(
            connection=connection,
            column_name='id',
            column_value=organization_id
        )

    def get_organization_by_code(self, connection, organization_code: str) -> Organization:
        return self._fetch_organization_by_column(
            connection=connection,
            column_name='code',
            column_value=organization_code
        )

    def get_all_organizations(self, connection) -> list[Organization]:
        organizations = []
        try:
            cursor = connection.cursor()
            sql = """
            SELECT o.id, o.code, o.name, o.created_at, o.updated_at 
            FROM organizations o
            """
            cursor.execute(sql)
            rows = cursor.fetchall()
            for row in rows:
                organizations.append(Organization.from_db_row(row))
            cursor.close()
        except Exception as e:
            traceback.print_exc()
        return organizations

    def update_organization(self, connection, organization_id: UUID, code: str = None, name: str = None) -> Organization:
        try:
            cursor = connection.cursor()
            update_fields = []
            params = []
            
            if code is not None:
                update_fields.append("code = %s")
                params.append(code)
            if name is not None:
                update_fields.append("name = %s")
                params.append(name)
                
            if update_fields:
                update_fields.append("updated_at = %s")
                params.append(datetime.now(UTC))
                params.append(organization_id)
                
                sql = f"""
                UPDATE organizations 
                SET {', '.join(update_fields)}
                WHERE id = %s
                RETURNING id, code, name, created_at, updated_at
                """
                cursor.execute(sql, params)
                row = cursor.fetchone()
                if row:
                    return Organization.from_db_row(row)
            cursor.close()
        except Exception as e:
            traceback.print_exc()
        return None

    def delete_organization(self, connection, organization_id: UUID) -> bool:
        try:
            cursor = connection.cursor()
            sql = "DELETE FROM organizations WHERE id = %s"
            cursor.execute(sql, [organization_id])
            deleted = cursor.rowcount > 0
            cursor.close()
            return deleted
        except Exception as e:
            traceback.print_exc()
            return False

    def _fetch_organization_by_column(self, connection, column_name: str, column_value: str | UUID) -> Organization:
        organization: Organization | None = None
        try:
            cursor = connection.cursor()
            sql = f"""
            SELECT o.id, o.code, o.name, o.created_at, o.updated_at 
            FROM organizations o WHERE o.{column_name} = %s
            """
            cursor.execute(sql, [column_value])
            row = cursor.fetchone()
            if row is not None:
                organization = Organization.from_db_row(row)
            cursor.close()
        except Exception as e:
            traceback.print_exc()
        return organization

    def _add_organization(self, connection, organization: Organization) -> UUID:
        sql = """
        INSERT INTO organizations (code, name, created_at, updated_at)
        VALUES (%s, %s, %s, %s) RETURNING id
        """
        cursor = connection.cursor()
        cursor.execute(
            sql, [
                organization.code,
                organization.name,
                organization.created_at,
                organization.updated_at
            ]
        )
        org_id = cursor.fetchone()[0]
        cursor.close()
        return org_id 