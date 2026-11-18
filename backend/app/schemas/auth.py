from pydantic import BaseModel, EmailStr, Field
class RegisterIn(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    role: str = 'machine_operator'
class LoginIn(BaseModel):
    email: EmailStr
    password: str
