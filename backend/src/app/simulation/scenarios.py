from pydantic import BaseModel, ConfigDict

from app.simulation.models import Mode


class Scenario(BaseModel):
    model_config = ConfigDict(frozen=True)

    mode: Mode
    prompt_file: str
    opening_line: str


SCENARIOS: dict[Mode, Scenario] = {
    Mode.DAILY_STANDUP: Scenario(
        mode=Mode.DAILY_STANDUP,
        prompt_file="tech_lead.md",
        opening_line=(
            "Good morning! Let's start our daily stand-up. "
            "What did you work on yesterday?"
        ),
    ),
}


def get_scenario(mode: Mode) -> Scenario:
    return SCENARIOS[mode]
