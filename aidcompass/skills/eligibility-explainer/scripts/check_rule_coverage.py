def missing_resource_ids(resource_ids: list[str], assessments: list[dict]) -> list[str]:
    covered = {item.get("resource_id") for item in assessments}
    return [resource_id for resource_id in resource_ids if resource_id not in covered]
