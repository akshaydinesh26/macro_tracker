from datetime import date
from typing import Self

from pydantic import BaseModel, Field, field_validator, model_validator


class HealthResponse:
    status: str = "Healthy"

class AvailableResponse(BaseModel):
    status: str
    sync_status: str
    sync_error: str | None = None

class DataPoint(BaseModel):
    datepoint: date
    value: float

class DataResponse(BaseModel):
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "indicator": "UNRATE",
                    "start_date": "2020-01-01",
                    "end_date": "2020-02-01",
                    "count": 2,
                    "data": [
                        {"date": "2020-01-01", "value": 3.5},
                        {"date": "2020-02-01", "value": 3.5},
                    ],
                }
            ]
        }
    }

    indicator: str
    start_date: date
    end_date: date
    count: int
    data: list[DataPoint]

class IndicatorsResponse(BaseModel):
    indicators: list[dict]

class DataRequest(BaseModel):
    model_config = {
        "json_schema_extra": {
            "examples": [
                {"indicator": "UNRATE", 
                 "start_date": "2020-01-01", 
                 "end_date": "2020-06-01"}
            ]
        }
    }

    indicator: str = Field(min_length=1)
    start_date: date
    end_date: date

    @field_validator("indicator")
    @classmethod
    def normalise_indicator(cls, value: str) -> str:
        return value.strip().upper()

    @model_validator(mode="after")
    def check_date_order(self) -> Self:
        if self.start_date > self.end_date:
            raise ValueError("start_date must be on or before end_date")
        return self