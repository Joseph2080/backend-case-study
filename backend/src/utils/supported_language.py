from typing import Literal, TypeGuard, get_args

# languages supported for backend localizations (e.g. CV, cover letter, etc.)
SupportedLanguage = Literal[
    "en", "de", "fr", "nl", "es", "sv", "pl", "it", "ro", "cs", "pt", "tr", "uk", "no", "fi", "da", "sk", "el", "hu", "bg", "hr"
]

SUPPORTED_LANGUAGES: set[str] = set(get_args(SupportedLanguage))


def is_supported_language(language: str) -> TypeGuard[SupportedLanguage]:
    return language in SUPPORTED_LANGUAGES
