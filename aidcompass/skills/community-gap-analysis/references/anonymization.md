# Anonymization rules

Allowed fields:

- timestamp rounded or bucketed for reporting
- need category
- barrier type
- unmet need category
- resource ID offered
- demo-data flag

Disallowed fields:

- raw message or summary
- name, phone, email or account ID
- exact address or coordinates
- health, immigration, legal, school or family narrative
- outreach draft text

Production dashboards should use minimum-count thresholds before showing small groups.
