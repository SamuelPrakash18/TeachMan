from pydantic import BaseModel, Field, model_validator

from app.schemas.auth import (
    DistrictStr,
    DoorNoStr,
    GradeStr,
    PersonNameStr,
    PinCodeStr,
    StateStr,
    StreetStr,
    SubjectStr,
    TeachingMode,
    TeachingTimingsStr,
    TuitionNameStr,
    UpiIdStr,
)


class TutorProfileOut(BaseModel):
    display_name: str
    phone: str
    public_id: str
    tuition_name: str
    door_no: str
    street: str
    district: str
    pin_code: str
    state: str
    subjects: list[str]
    grades: list[str]
    teaching_timings: str
    teaching_mode: TeachingMode
    upi_id: str | None = None


class TutorProfileUpdate(BaseModel):
    display_name: PersonNameStr | None = None
    tuition_name: TuitionNameStr | None = None
    door_no: DoorNoStr | None = None
    street: StreetStr | None = None
    district: DistrictStr | None = None
    pin_code: PinCodeStr | None = None
    state: StateStr | None = None
    subjects: list[SubjectStr] | None = Field(default=None, min_length=1)
    grades: list[GradeStr] | None = Field(default=None, min_length=1)
    teaching_timings: TeachingTimingsStr | None = None
    teaching_mode: TeachingMode | None = None
    upi_id: UpiIdStr | None = None

    @model_validator(mode="after")
    def reject_null_for_required_fields(self) -> "TutorProfileUpdate":
        for name in self.model_fields_set:
            if name != "upi_id" and getattr(self, name) is None:
                raise ValueError(f"{name} cannot be null")
        return self
