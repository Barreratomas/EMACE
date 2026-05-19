from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from .user import UserResponse

class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None
    permissions: List[str] = []

class RoleCreate(RoleBase):
    pass

class RoleResponse(RoleBase):
    model_config = ConfigDict(from_attributes=True)
    id: int

class IAMPolicyBase(BaseModel):
    name: str
    description: Optional[str] = None
    permissions: List[str] = []

class IAMPolicyCreate(IAMPolicyBase):
    pass

class IAMPolicyResponse(IAMPolicyBase):
    model_config = ConfigDict(from_attributes=True)
    id: int

class IAMUserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=12)
    name: str

class IAMUserResponse(UserResponse):
    parent_id: int

class IAMPolicyAssignRequest(BaseModel):
    policies: List[str]
    operation: str = Field(default="set")  # set | add | remove
