from pydantic import BaseModel

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None

class AdminUserResponse(BaseModel):
    id: int
    username: str

    class Config:
        from_attributes = True
