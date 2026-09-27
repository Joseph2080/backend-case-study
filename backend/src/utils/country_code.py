from typing import Annotated, Any

from pydantic import BeforeValidator, Field


def _normalize_country_code(value: Any) -> Any:
    if isinstance(value, str):
        return value.strip().upper()
    return value


CountryCode = Annotated[str, BeforeValidator(_normalize_country_code), Field(min_length=2, max_length=2, pattern=r"^[A-Z]{2}$")]
