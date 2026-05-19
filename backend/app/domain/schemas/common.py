from pydantic import BaseModel

class Msg(BaseModel):
    msg: str

class GenericResponse(BaseModel):
    ok: bool
    message: str
