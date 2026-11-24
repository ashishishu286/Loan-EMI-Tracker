from pydantic import BaseModel, Field, field_validator


class LoginRequest(BaseModel):
    username: str
    password: str


class MemberCreate(BaseModel):
    member_code: str = Field(..., min_length=1, max_length=30)
    name: str = Field(..., min_length=1, max_length=100)
    monthly_salary: int = Field(..., gt=0)

    @field_validator("member_code", "name")
    @classmethod
    def strip_non_empty(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Field cannot be blank")
        return cleaned


class LoanCreate(BaseModel):
    member_id: int = Field(..., gt=0)
    principal: int = Field(..., gt=0, le=100_000_000)
    tenure_months: int = Field(..., ge=1, le=360)