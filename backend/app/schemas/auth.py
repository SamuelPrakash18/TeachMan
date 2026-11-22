from typing import Annotated, Literal
import uuid

from pydantic import BaseModel, Field, StringConstraints, model_validator

PhoneStr = Annotated[str, StringConstraints(strip_whitespace=True, pattern=r"^\d{10}$")]
PinCodeStr = Annotated[str, StringConstraints(strip_whitespace=True, pattern=r"^\d{6}$")]
PersonNameStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=120)]
TuitionNameStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=150)]
DoorNoStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=20)]
StreetStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
DistrictStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
StateStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
SubjectStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)]
GradeStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=20)]
TeachingTimingsStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]
UpiIdStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
AddressStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]
PasswordStr = Annotated[str, StringConstraints(min_length=8, max_length=128)]
TeachingMode = Literal["offline", "online", "hybrid"]


class TutorRegisterIn(BaseModel):
    name: PersonNameStr
    phone: PhoneStr
    password: PasswordStr
    confirm_password: str = Field(..., min_length=1, max_length=128)
    tuition_name: TuitionNameStr
    door_no: DoorNoStr
    street: StreetStr
    district: DistrictStr
    pin_code: PinCodeStr
    state: StateStr
    subjects: list[SubjectStr] = Field(..., min_length=1)
    grades: list[GradeStr] = Field(..., min_length=1)
    teaching_timings: TeachingTimingsStr
    teaching_mode: TeachingMode
    upi_id: UpiIdStr | None = None

    @model_validator(mode="after")
    def check_passwords_match(self) -> "TutorRegisterIn":
        if self.password != self.confirm_password:
            raise ValueError("passwords do not match")
        return self


class ParentRegisterIn(BaseModel):
    name: PersonNameStr
    phone: PhoneStr
    password: PasswordStr
    confirm_password: str = Field(..., min_length=1, max_length=128)
    student_name: PersonNameStr
    student_grade: GradeStr
    student_address: AddressStr

    @model_validator(mode="after")
    def check_passwords_match(self) -> "ParentRegisterIn":
        if self.password != self.confirm_password:
            raise ValueError("passwords do not match")
        return self


class LoginIn(BaseModel):
    phone: str = Field(..., min_length=10, max_length=15)
    password: str = Field(..., min_length=1, max_length=128)


class ChangePasswordIn(BaseModel):
    current_password: str = Field(..., min_length=1, max_length=128)
    new_password: PasswordStr


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    public_id: str | None = None


class UserOut(BaseModel):
    id: uuid.UUID
    phone: str
    role: str
    public_id: str | None = None
    display_name: str | None = None
