import pytest

from app.simulation.models import Mode
from app.simulation.scenarios import get_scenario


@pytest.mark.parametrize("mode", list(Mode))
def test_every_mode_has_a_scenario(mode: Mode):
    scenario = get_scenario(mode)
    assert scenario.mode is mode
    assert scenario.opening_line.strip()
    assert scenario.prompt_file.endswith(".md")
