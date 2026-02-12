from pydantic import BaseModel


class ModulesResponse(BaseModel):
    features: list[str]


class UpdateModulesRequest(BaseModel):
    features: list[str]
