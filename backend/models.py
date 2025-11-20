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


class GeneratePDFRequest(BaseModel):
    csv_data: str = Field(..., description="CSV data as string")
    title: str = Field(default="Data Report", description="Report title")
    report_description: Optional[str] = Field(None, description="Optional report description")


class GeneratePDFResponse(BaseModel):
    pdf_data: str = Field(..., description="PDF file as base64 encoded string")
    file_name: str = Field(..., description="Suggested file name for the PDF")
    status: str = Field(...)

