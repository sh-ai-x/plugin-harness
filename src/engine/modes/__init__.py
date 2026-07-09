"""Mode registry for the interview engine.

PR #22 review (🟠 major #3): VALID_MODES was previously duplicated as
two independent tuple literals across cli.py and runner.py. The mode
list is a single source of truth and lives here. Both cli.py and
runner.py should import MODES from this module.
"""

__all__ = ["MODES"]


MODES: tuple[str, ...] = (
    "user",
    "ai-research",
)
