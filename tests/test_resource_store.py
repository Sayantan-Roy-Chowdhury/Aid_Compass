from aidcompass.schemas import (
    AgeBand,
    NeedCategory,
    NeedItem,
    SupportPreferences,
    SupportProfile,
)
from aidcompass.tools.resource_store import ResourceStore


def test_resource_search_finds_evening_tutoring():
    profile = SupportProfile(
        safe_summary="Teen needs free math tutoring after school.",
        location_text="Scarborough",
        age_band=AgeBand.AGE_13_17,
        needs=[
            NeedItem(
                category=NeedCategory.EDUCATION_SUPPORT,
                statement="free math help",
                keywords=["math", "tutoring", "evening"],
            )
        ],
        preferences=SupportPreferences(
            free_only=True,
            preferred_times=["after 17:00"],
        ),
    )
    candidates, trace, location, *_ = ResourceStore().search(profile, max_candidates=10)
    ids = {candidate.resource.resource_id for candidate in candidates}
    assert "edu_northstar_001" in ids
    assert "study_online_018" in ids
    assert location == "Scarborough"
    assert trace


def test_online_only_filters_in_person_only_resources():
    profile = SupportProfile(
        safe_summary="Needs online study support.",
        location_text="Scarborough",
        age_band=AgeBand.AGE_13_17,
        needs=[NeedItem(category=NeedCategory.EDUCATION_SUPPORT, statement="study help")],
        preferences=SupportPreferences(online_only=True, delivery_modes=["online"]),
    )
    candidates, *_ = ResourceStore().search(profile, max_candidates=20)
    assert candidates
    assert all("online" in candidate.resource.delivery_modes for candidate in candidates)


def test_in_person_only_unknown_city_does_not_return_remote_records():
    profile = SupportProfile(
        safe_summary="Needs in-person disability support in Halifax.",
        location_text="Halifax",
        needs=[
            NeedItem(
                category=NeedCategory.DISABILITY_SUPPORT,
                statement="in-person disability support",
            )
        ],
        preferences=SupportPreferences(delivery_modes=["in_person"]),
    )
    candidates, *_ = ResourceStore().search(profile, max_candidates=20)
    assert candidates == []
