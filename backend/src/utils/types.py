"""Custom type definitions with validation for the application."""

import re
from typing import Annotated

from pydantic import AfterValidator


def _validate_hex_color(value: str) -> str:
    """
    Validate and normalize hex color code.

    Accepts colors in formats:
    - #RRGGBB or #rrggbb (with hash)
    - RRGGBB or rrggbb (without hash - will be added)

    Returns normalized uppercase format: #RRGGBB

    Raises:
        ValueError: If the color format is invalid
    """
    if not value:
        raise ValueError("Color cannot be empty")

    # Strip whitespace and convert to uppercase
    color = value.strip().upper()

    # Add # if missing
    if not color.startswith("#"):
        color = f"#{color}"

    # Validate format: exactly 7 characters (#RRGGBB)
    if len(color) != 7:
        raise ValueError(f"Color must be exactly 7 characters in #RRGGBB format, got {len(color)} characters: {color}")

    # Validate hex digits
    hex_pattern = re.compile(r"^#[0-9A-F]{6}$")
    if not hex_pattern.match(color):
        raise ValueError(f"Invalid hex color format: {color}. Must be #RRGGBB where R, G, B are hex digits (0-9, A-F)")

    return color


# HexColor type for required hex colors (always returns valid #RRGGBB string)
HexColor = Annotated[str, AfterValidator(_validate_hex_color)]
