from typing import Any, Dict

from pydantic import BaseModel


def to_lower_camel(string: str) -> str:
    """
    Converts a string to lowerCamelCase.
    Args:
        string: string to be camel cased.
    Returns:
        string in lowerCamelCase
    """
    words = string.split("_")
    return words[0] + "".join(word.capitalize() for word in words[1:])


class AppBaseModel(BaseModel):

    def dict(self, *args, **kwargs) -> Dict[str, Any]:
        """
        Default BaseModel includes missing, and none values.
        https://github.com/tiangolo/fastapi/issues/3314
        """
        kwargs.pop("exclude_none")
        return super().dict(*args, exclude_none=True, **kwargs)

    class Config:
        """
        Custom Config for ConsentBaseModel
        - lower camel case for request/responses
        Ref:
        - https://pydantic-docs.helpmanual.io/usage/model_config/#alias-generator
        - https://pydantic-docs.helpmanual.io/mypy_plugin/#generate-a-signature-for-model__init__
        """

        alias_generator = to_lower_camel
        populate_by_name = True
        arbitrary_types_allowed = True


class TokenExchangeRequest(AppBaseModel):
    id_token: str
