from pydantic import BaseModel


class CSVRowError(BaseModel):
    row: int
    field: str
    message: str


class ErrorResponse(BaseModel):
    errors: list[CSVRowError]
