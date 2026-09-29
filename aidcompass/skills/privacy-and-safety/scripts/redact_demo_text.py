import re

EMAIL = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
PHONE = re.compile(r"(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)\d{3}[-.\s]?\d{4}")


def redact(text: str) -> str:
    text = EMAIL.sub("[email omitted]", text)
    return PHONE.sub("[phone omitted]", text)
