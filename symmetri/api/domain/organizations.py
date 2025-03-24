import datetime
import json
from uuid import UUID


class Organization(object):

    def __init__(self, code: str, name: str,
                 created_at: datetime.datetime = None, updated_at: datetime.datetime = None,
                 organization_id: UUID = None):
        self.code = code
        self.name = name
        self.organization_id = organization_id
        self.created_at = created_at
        self.updated_at = updated_at

    def __str__(self):
        return json.dumps({
            'organization_id': str(self.organization_id),
            'code': self.code,
            'name': self.name,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        })

    @staticmethod
    def from_db_row(row):
        return Organization(
            organization_id=row[0],
            code=row[1],
            name=row[2],
            created_at=row[3],
            updated_at=row[4]
        )

    @staticmethod
    def clone_with_id(org, db_org_id):
        return Organization(
            organization_id=db_org_id,
            code=org.code,
            name=org.name,
            created_at=org.created_at,
            updated_at=org.updated_at
        ) 