import pytest
from pydantic import ValidationError

from app.feedback.models import Correction


def test_valid_correction():
    c = Correction(original="I go", corrected="I went", explanation="Past tense.")
    assert c.corrected == "I went"


@pytest.mark.parametrize("field", ["original", "corrected", "explanation"])
def test_blank_fields_are_rejected(field: str):
    data = {"original": "I go", "corrected": "I went", "explanation": "Past tense."}
    data[field] = "   "
    with pytest.raises(ValidationError):
        Correction(**data)


def test_correction_must_change_something():
    with pytest.raises(ValidationError):
        Correction(original="I went", corrected="I went", explanation="Nothing.")
