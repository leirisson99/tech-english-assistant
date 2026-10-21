from typing import Annotated, Self

from pydantic import BaseModel, StringConstraints, model_validator

NonBlank = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class NoUserSpeechError(Exception):
    """There is nothing from the user to give feedback on."""


class Correction(BaseModel):
    original: NonBlank
    corrected: NonBlank
    explanation: NonBlank

    @model_validator(mode="after")
    def _must_change_something(self) -> Self:
        if self.original == self.corrected:
            raise ValueError("a correction must differ from the original text")
        return self


class SessionFeedback(BaseModel):
    corrections: list[Correction]
    better_phrasing: list[str]
    vocabulary: list[str]
    overall_comment: str
