import traceback
from uuid import UUID

from symmetri.api.db.organization_repository import OrganizationRepository
from symmetri.api.domain.organizations import Organization
from symmetri.db.base import DbProvider
from symmetri.symmetri_logger import logger


class OrganizationManagementService(object):

    def __init__(self, db_provider: DbProvider):
        self.organization_repository = OrganizationRepository()
        self.db_provider = db_provider

    def create_organization(self, organization: Organization) -> Organization:
        logger.info("*** OrganizationManagementService => create_organization ***")
        logger.info("code = %s, name = %s" % (organization.code, organization.name))
        connection = self.db_provider.get_default_connection()
        new_org: Organization | None = None
        try:
            new_org = self.organization_repository.create_organization(connection, organization)
            connection.commit()
        except Exception as e:
            traceback.print_exc()
            connection.rollback()
        finally:
            connection.close()
        return new_org

    def get_organization_by_id(self, organization_id: UUID) -> Organization:
        connection = self.db_provider.get_default_connection()
        organization: Organization | None = None
        try:
            organization = self.organization_repository.get_organization_by_id(
                connection=connection,
                organization_id=organization_id
            )
        except Exception as e:
            traceback.print_exc()
        finally:
            connection.close()
        return organization
    
    def get_organization_by_code(self, organization_code: str) -> Organization:
        connection = self.db_provider.get_default_connection()
        organization: Organization | None = None
        try:
            organization = self.organization_repository.get_organization_by_code(
                connection=connection,
                organization_code=organization_code
            )
        except Exception as e:
            traceback.print_exc()
        finally:
            connection.close()
        return organization

    def get_all_organizations(self) -> list[Organization]:
        connection = self.db_provider.get_default_connection()
        organizations = []
        try:
            organizations = self.organization_repository.get_all_organizations(connection)
        except Exception as e:
            traceback.print_exc()
        finally:
            connection.close()
        return organizations

    def update_organization(self, organization_id: UUID, code: str = None, name: str = None) -> Organization:
        connection = self.db_provider.get_default_connection()
        updated_org: Organization | None = None
        try:
            updated_org = self.organization_repository.update_organization(
                connection=connection,
                organization_id=organization_id,
                code=code,
                name=name
            )
            connection.commit()
        except Exception as e:
            traceback.print_exc()
            connection.rollback()
        finally:
            connection.close()
        return updated_org

    def delete_organization(self, organization_id: UUID) -> bool:
        connection = self.db_provider.get_default_connection()
        success = False
        try:
            success = self.organization_repository.delete_organization(
                connection=connection,
                organization_id=organization_id
            )
            connection.commit()
        except Exception as e:
            traceback.print_exc()
            connection.rollback()
        finally:
            connection.close()
        return success 