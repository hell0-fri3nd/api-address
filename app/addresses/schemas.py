from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100
MAX_DISTANCE_KM = 20000

INPUT_CONFIG = ConfigDict(extra="forbid", str_strip_whitespace=True)


class AddressCreate(BaseModel):
    model_config = INPUT_CONFIG

    street: str = Field(min_length=1, max_length=255)
    city: str = Field(min_length=1, max_length=100)
    state: str | None = Field(default=None, min_length=1, max_length=100)
    postal_code: str | None = Field(default=None, min_length=1, max_length=20)
    country: str = Field(min_length=1, max_length=100)
    latitude: float = Field(ge=-90, le=90, allow_inf_nan=False)
    longitude: float = Field(ge=-180, le=180, allow_inf_nan=False)


class AddressUpdate(BaseModel):
    model_config = INPUT_CONFIG

    street: str | None = Field(default=None, min_length=1, max_length=255)
    city: str | None = Field(default=None, min_length=1, max_length=100)
    state: str | None = Field(default=None, min_length=1, max_length=100)
    postal_code: str | None = Field(default=None, min_length=1, max_length=20)
    country: str | None = Field(default=None, min_length=1, max_length=100)
    latitude: float | None = Field(default=None, ge=-90, le=90, allow_inf_nan=False)
    longitude: float | None = Field(
        default=None,
        ge=-180,
        le=180,
        allow_inf_nan=False,
    )

    @model_validator(mode="after")
    def check_fields(self) -> "AddressUpdate":
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided")

        required = {"street", "city", "country", "latitude", "longitude"}
        nulls = sorted(
            field
            for field in required & self.model_fields_set
            if getattr(self, field) is None
        )

        if nulls:
            raise ValueError(f"{', '.join(nulls)} cannot be null")

        return self


class AddressRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    street: str
    city: str
    state: str | None
    postal_code: str | None
    country: str
    latitude: float
    longitude: float
    created_at: datetime
    updated_at: datetime


class AddressNearbyRead(AddressRead):
    distance_km: float


class ListParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    limit: int = Field(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE)
    offset: int = Field(default=0, ge=0)


class NearbyParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

    latitude: float = Field(ge=-90, le=90, allow_inf_nan=False)
    longitude: float = Field(ge=-180, le=180, allow_inf_nan=False)
    distance_km: float = Field(gt=0, le=MAX_DISTANCE_KM, allow_inf_nan=False)
    limit: int = Field(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE)
