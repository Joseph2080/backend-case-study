import enum
import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING, ClassVar

from sqlalchemy import CheckConstraint
from sqlalchemy.orm import Mapped
from sqlmodel import Field, Relationship, SQLModel

from src.cv.views.style import CVDatePosition, CVTextAlignment
from src.db.mixins import utc_created_at_field, utc_updated_at_field
from src.utils.country_code import CountryCode
from src.utils.supported_language import SupportedLanguage
from src.utils.types import HexColor

if TYPE_CHECKING:  # pragma: no cover - for type checking only, avoids import cycles at runtime
    from src.cv.models.cv_section import CVSectionModel


class CVLanguage(str, enum.Enum):
    en = "en"
    de = "de"
    fr = "fr"
    nl = "nl"
    es = "es"
    sv = "sv"
    pl = "pl"
    it = "it"
    ro = "ro"
    cs = "cs"
    pt = "pt"
    tr = "tr"
    uk = "uk"
    no = "no"
    fi = "fi"
    da = "da"
    sk = "sk"
    el = "el"
    hu = "hu"
    bg = "bg"
    hr = "hr"

    @property
    def language_code(self) -> SupportedLanguage:
        return self.value

    @staticmethod
    def from_language_code(language_code: SupportedLanguage) -> "CVLanguage":
        match language_code:  # to ensure type-safety
            case "en":
                return CVLanguage.en
            case "de":
                return CVLanguage.de
            case "fr":
                return CVLanguage.fr
            case "nl":
                return CVLanguage.nl
            case "es":
                return CVLanguage.es
            case "sv":
                return CVLanguage.sv
            case "pl":
                return CVLanguage.pl
            case "it":
                return CVLanguage.it
            case "ro":
                return CVLanguage.ro
            case "cs":
                return CVLanguage.cs
            case "pt":
                return CVLanguage.pt
            case "tr":
                return CVLanguage.tr
            case "uk":
                return CVLanguage.uk
            case "no":
                return CVLanguage.no
            case "fi":
                return CVLanguage.fi
            case "da":
                return CVLanguage.da
            case "sk":
                return CVLanguage.sk
            case "el":
                return CVLanguage.el
            case "hu":
                return CVLanguage.hu
            case "bg":
                return CVLanguage.bg
            case "hr":
                return CVLanguage.hr


class DatePosition(str, enum.Enum):
    leading = "leading"
    trailing = "trailing"

    @staticmethod
    def from_string(date_position: CVDatePosition) -> "DatePosition":
        match date_position:
            case "leading":
                return DatePosition.leading
            case "trailing":
                return DatePosition.trailing


class TextAlignment(str, enum.Enum):
    leading = "leading"
    justify = "justify"

    @staticmethod
    def from_string(text_alignment: CVTextAlignment) -> "TextAlignment":
        match text_alignment:
            case "leading":
                return TextAlignment.leading
            case "justify":
                return TextAlignment.justify


class CVModel(SQLModel, table=True):
    __tablename__: ClassVar[str] = "cvs"
    __table_args__: ClassVar[tuple] = (
        CheckConstraint(
            "target_country_code ~ '^[A-Z]{2}$'",
            name="check_cvs_target_country_code_uppercase",
        ),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: str = Field(..., index=True)

    # CV metadata
    cv_name: str | None = Field(default=None, description="User-defined name for the CV")

    cv_language: CVLanguage = Field(default=CVLanguage.en)  # iso 639-1 code
    target_country_code: CountryCode | None = Field(default=None, description="ISO 3166-1 alpha-2 country code this CV is optimized for")

    # person details
    first_name: str = Field(...)
    last_name: str = Field(...)
    email: str | None = Field(default=None)
    phone: str | None = Field(default=None)

    street_address: str | None = Field(default=None)
    city: str | None = Field(default=None)
    state: str | None = Field(default=None)
    postal_code: str | None = Field(default=None)
    country: str | None = Field(...)

    date_of_birth: date | None = Field(default=None)
    driving_license: str | None = Field(default=None)
    place_of_birth: str | None = Field(default=None)
    nationality: str | None = Field(default=None)
    personal_website: str | None = Field(default=None)
    marital_status: str | None = Field(default=None)
    professional_title: str | None = Field(default=None)

    professional_summary: str | None = Field(default=None)

    privacy_clause_enabled: bool = Field(default=False)

    # Signature settings
    signature_enabled: bool = Field(default=False)
    signature_location: str | None = Field(default=None)
    signature_include_date: bool = Field(default=True)
    signature_show_name: bool = Field(default=False)

    # Style settings
    template_id: str | None = Field(default=None)
    accent_color: HexColor | None = Field(default=None, max_length=7, description="Hex color code for CV styling (#RRGGBB)")

    section_spacing: float | None = Field(default=None, ge=0.7, le=1.3)
    line_spacing: float | None = Field(default=None, ge=0.7, le=1.3)
    margin_spacing: float | None = Field(default=None, ge=0.7, le=1.3)
    date_position: DatePosition | None = Field(default=None)
    text_alignment: TextAlignment | None = Field(default=None)

    # font style settings
    font_size: float | None = Field(default=None, ge=0.7, le=1.3)
    font_family: str | None = Field(default=None, max_length=64)
    content_font_scale: float | None = Field(default=None, ge=0.7, le=1.4)
    heading_font_scale: float | None = Field(default=None, ge=0.7, le=1.4)

    # CV hierarchy
    parent_cv_id: uuid.UUID | None = Field(
        default=None,
        foreign_key="cvs.id",
        ondelete="SET NULL",  # If parent is deleted, child becomes orphaned but remains
    )

    # Relationships
    sections: Mapped[list["CVSectionModel"]] = Relationship(
        back_populates="cv", cascade_delete=True, sa_relationship_kwargs={"order_by": "CVSectionModel.position"}
    )

    created_at: datetime = utc_created_at_field()
    updated_at: datetime = utc_updated_at_field()
