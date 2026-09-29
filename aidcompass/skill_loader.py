"""Filesystem-backed ADK SkillToolset helpers."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from google.adk.skills import load_skill_from_dir
from google.adk.skills.models import Skill
from google.adk.tools import skill_toolset


SKILLS_ROOT = Path(__file__).resolve().parent / "skills"


@lru_cache(maxsize=None)
def load_skill(name: str) -> Skill:
    return load_skill_from_dir(SKILLS_ROOT / name)


def make_skill_toolset(*names: str) -> skill_toolset.SkillToolset:
    return skill_toolset.SkillToolset(skills=[load_skill(name) for name in names])


def available_skill_names() -> list[str]:
    return sorted(path.name for path in SKILLS_ROOT.iterdir() if path.is_dir())
