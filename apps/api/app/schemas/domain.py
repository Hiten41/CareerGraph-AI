from typing import Literal
from pydantic import BaseModel, Field, ConfigDict, model_validator


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Profile(Strict):
    name: str = Field(default="", max_length=120)
    skills: list[str] = Field(default_factory=list, max_length=100)
    graduation_year: int | None = Field(default=None, ge=1950, le=2100)
    experience_years: float | None = Field(default=None, ge=0, le=80)
    experience: list[str] = Field(default_factory=list, max_length=30)
    projects: list[str] = Field(default_factory=list, max_length=30)
    education: list[str] = Field(default_factory=list, max_length=30)
    languages: list[str] = Field(default_factory=list, max_length=30)
    evidence: dict[str, str] = Field(default_factory=dict)


WorkMode = Literal["remote", "onsite", "hybrid"]
Employment = Literal["internship", "full-time"]


class Constraints(Strict):
    exclude_mode: list[WorkMode] | None = Field(default=None, max_length=3)
    exclude_employment: list[Employment] | None = Field(default=None, max_length=2)
    verified_only: bool | None = None
    employment: Employment | None = None
    mode: WorkMode | None = None
    location: str | None = Field(default=None, max_length=100)
    graduation_year: int | None = Field(default=None, ge=1950, le=2100)
    min_salary: float | None = Field(default=None, ge=0)
    currency: Literal["INR", "USD", "EUR"] | None = None
    period: Literal["month", "year", "hour"] | None = None
    max_experience: float | None = Field(default=None, ge=0)
    domain: str | None = Field(default=None, max_length=80)

    @model_validator(mode="after")
    def no_conflicting_exclusions(self):
        for field in ("mode", "employment"):
            included = getattr(self, field)
            if included in (getattr(self, f"exclude_{field}") or []):
                raise ValueError(f"{included} is both required and excluded")
        return self


class Search(Strict):
    query: str = Field(min_length=1, max_length=1000)
    constraints: Constraints = Field(default_factory=Constraints)
    strategy: Literal["keyword", "semantic", "hybrid", "personalized"] = "personalized"
    limit: int = Field(default=10, ge=1, le=50)
    offset: int = Field(default=0, ge=0, le=500)


class Job(Strict):
    source: str = Field(max_length=100)
    external_id: str = Field(max_length=150)
    title: str = Field(min_length=1, max_length=200)
    company: str = Field(max_length=200)
    description: str = Field(max_length=20000)
    skills: list[str] = Field(default_factory=list, max_length=100)
    optional_skills: list[str] = Field(default_factory=list, max_length=100)
    employment: Employment | None = None
    mode: WorkMode | None = None
    location: str | None = None
    graduation_year: int | None = None
    salary: float | None = Field(default=None, ge=0)
    currency: Literal["INR", "USD", "EUR"] | None = None
    period: Literal["month", "year", "hour"] | None = None
    experience: float | None = Field(default=None, ge=0)
    domain: str | None = None
    status: Literal["active", "expired", "unknown", "archived"] = "active"
    url: str = Field(pattern=r"^https://", max_length=2000)
    synthetic: bool = True
