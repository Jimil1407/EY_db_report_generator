"""
Pydantic models for request and response schemas.
"""
from pydantic import BaseModel, Field
from typing import Optional


class GenerateSQLRequest(BaseModel):
    user_name: str = Field(...)
    user_email: str = Field(...)
    query: str = Field(...)


class GenerateSQLResponse(BaseModel):
    user_name: str = Field(...)
    user_email: str = Field(...)
    sql_query: str = Field(...)
    selected_tables: list = Field(default_factory=list)  # List of selected table names
    status: str = Field(...)


class ExecuteQueryRequest(BaseModel):
    sql_query: str = Field(...)


class ExecuteQueryResponse(BaseModel):
    results: list = Field(...)
    columns: list = Field(...)
    row_count: int = Field(...)
    error: Optional[str] = Field(None)
    status: str = Field(...)

