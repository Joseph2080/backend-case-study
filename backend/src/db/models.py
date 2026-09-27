# Import all models here to ensure they are registered with SQLModel
# This file must be imported before creating database tables

from sqlalchemy.orm import configure_mappers

from src.career_details.models import CareerDetailsModel, WorkExperienceModel
from src.cv.models.cv import CVModel
from src.cv.models.cv_attribute import CVAttributeModel
from src.cv.models.cv_item import CVItemModel
from src.cv.models.cv_section import CVSectionModel

configure_mappers()  # ensure the mapping is done as soon as possible, to get errors right away


__all__ = [
    "CVModel",
    "CVSectionModel",
    "CVAttributeModel",
    "CVItemModel",
    "WorkExperienceModel",
    "CareerDetailsModel",
]
