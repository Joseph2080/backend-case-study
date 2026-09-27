from uuid import UUID

from sqlmodel import select

from src.cv._conversion.service import CVDatabaseConversionService
from src.cv._sync.utils import sync_model_fields
from src.cv.models.cv import CVModel
from src.cv.models.cv_section import CVSectionModel
from src.cv.views.cv_data import CVData
from src.db import selectinload
from src.db.service import AsyncSession, DatabaseService
from src.db.utils.wrapper import with_database_session
from src.utils.classes import singleton
from src.utils.utils import dedup_identifiable_sorted_items


@singleton
class CVDatabaseSyncService:
    def __init__(self):
        self.db_service = DatabaseService()
        self.conversion_service = CVDatabaseConversionService()

    @with_database_session
    async def sync_to_database(self, session: AsyncSession, cv_data: CVData) -> CVModel:
        """Sync CV data to the database and return the updated CV model."""
        cv_model = await self._get_full_cv_model(cv_data.id, session)
        new_cv_model = self.conversion_service.convert_cv_data_to_model(cv_data, cv_model.user_id)

        # Sync all non-relationship fields from new model to existing model
        sync_model_fields(new_cv_model, cv_model)

        existing_section_ids = {section.id for section in cv_model.sections}
        new_section_ids = {section.id for section in new_cv_model.sections}
        removed_section_ids = existing_section_ids - new_section_ids
        added_section_ids = new_section_ids - existing_section_ids
        updated_section_ids = existing_section_ids & new_section_ids

        # Rebind only sections that are truly new to this CV to the attached parent
        for section in new_cv_model.sections:
            if section.id in added_section_ids:
                section.cv = cv_model
                section.cv_id = cv_model.id
                # Ensure children are attached to this section instance explicitly
                for item in section.items:
                    item.section = section
                    item.section_id = section.id
                for attribute in section.attributes:
                    attribute.section = section
                    attribute.section_id = section.id

        # remove & add new sections
        cv_model.sections = [s for s in cv_model.sections if s.id not in removed_section_ids]
        cv_model.sections.extend([s for s in new_cv_model.sections if s.id in added_section_ids])

        # update existing sections
        for section in cv_model.sections:
            if section.id in updated_section_ids:
                new_section = next((s for s in new_cv_model.sections if s.id == section.id), None)
                assert new_section is not None, f"New section with id {section.id} not found"

                # Update inner fields of CVSectionModel
                sync_model_fields(new_section, section)

                # update items
                existing_item_ids = {item.id for item in section.items}
                new_item_ids = {item.id for item in new_section.items}
                removed_item_ids = existing_item_ids - new_item_ids
                added_item_ids = new_item_ids - existing_item_ids
                updated_item_ids = existing_item_ids & new_item_ids

                # remove & add new items
                section.items = [i for i in section.items if i.id not in removed_item_ids]
                # Rebind new items to the existing attached section before appending
                new_items_to_add = [i for i in new_section.items if i.id in added_item_ids]
                for i in new_items_to_add:
                    i.section = section
                    i.section_id = section.id
                section.items.extend(new_items_to_add)

                # update existing items
                for item in section.items:
                    if item.id in updated_item_ids:
                        new_item = next((i for i in new_section.items if i.id == item.id), None)
                        assert new_item is not None, f"New item with id {item.id} not found"

                        # Update inner fields of CVItemModel
                        sync_model_fields(new_item, item)

                # update attributes
                existing_attribute_ids = {attribute.id for attribute in section.attributes}
                new_attribute_ids = {attribute.id for attribute in new_section.attributes}
                removed_attribute_ids = existing_attribute_ids - new_attribute_ids
                added_attribute_ids = new_attribute_ids - existing_attribute_ids
                updated_attribute_ids = existing_attribute_ids & new_attribute_ids

                # remove & add new attributes
                section.attributes = [a for a in section.attributes if a.id not in removed_attribute_ids]
                new_attributes_to_add = [a for a in new_section.attributes if a.id in added_attribute_ids]
                for a in new_attributes_to_add:
                    a.section = section
                    a.section_id = section.id
                section.attributes.extend(new_attributes_to_add)

                # update existing attributes
                for attribute in section.attributes:
                    if attribute.id in updated_attribute_ids:
                        new_attribute = next((a for a in new_section.attributes if a.id == attribute.id), None)
                        assert new_attribute is not None, f"New attribute with id {attribute.id} not found"

                        # Update inner fields of CVAttributeModel
                        sync_model_fields(new_attribute, attribute)

                # dedup items and attributes, which happens due to setting `.section` and also `.extend()` (which is however both required for various reasons)  # noqa: E501
                # needed to be able to use returned model as e.g. API response
                section.items = sorted(dedup_identifiable_sorted_items(section.items), key=lambda item: item.position)
                section.attributes = sorted(dedup_identifiable_sorted_items(section.attributes), key=lambda attribute: attribute.position)

        await session.commit()

        return cv_model

    # region: - Helpers

    async def _get_full_cv_model(self, cv_id: UUID, session: AsyncSession) -> CVModel:
        return await self.db_service.get_first_in_or_throw(
            select(CVModel)
            .where(CVModel.id == cv_id)
            .options(
                selectinload(CVModel.sections).selectinload(CVSectionModel.items),
                selectinload(CVModel.sections).selectinload(CVSectionModel.attributes),
            ),
            session,
        )

    # endregion
