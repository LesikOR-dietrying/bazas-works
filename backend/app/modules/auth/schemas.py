from pydantic import BaseModel, ConfigDict, Field, SecretStr

from app.modules.users.schemas import Username


class Login(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: Username
    password: SecretStr = Field(min_length=1, max_length=128)
