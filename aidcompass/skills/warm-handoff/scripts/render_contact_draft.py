def render(template: str, **values: str) -> str:
    return template.format(**values)
