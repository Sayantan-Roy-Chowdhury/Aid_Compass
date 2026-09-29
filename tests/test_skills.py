from aidcompass.skill_loader import available_skill_names, load_skill


def test_every_skill_loads_and_has_three_level_content():
    names = available_skill_names()
    assert len(names) >= 8
    for name in names:
        skill = load_skill(name)
        assert skill.name == name
        assert skill.description
        assert skill.instructions.strip()
        assert skill.resources.references
        assert skill.resources.assets
        assert skill.resources.scripts
