from typing import TypeVar

from sqlmodel import SQLModel

T = TypeVar("T", bound=SQLModel)


def sync_model_fields(
    source: T,
    target: T,
    exclude_fields: set[str] | None = None,
    include_only: set[str] | None = None,
    exclude_defaults: bool = True,
):
    """
    Synchronize fields from source model to target model.

    This function copies field values from source to target, intelligently
    handling SQLModel instances. It's designed to be resilient to schema changes.

    Default exclusions (when exclude_defaults=True):
        - id: Preserves the unique identifier
        - *_id: Preserves all foreign key relationships
        - created_at: Preserves original creation timestamp
        - updated_at: Preserves update timestamp

    Args:
        source: The source SQLModel instance to copy fields from
        target: The target SQLModel instance to copy fields to
        exclude_fields: Set of field names to exclude from synchronization (in addition to defaults)
        include_only: If provided, only sync these specific fields
        exclude_defaults: If True (default), automatically excludes common timestamp fields
    """
    if exclude_fields is None:
        exclude_fields = set()

    # Get all model fields from the source
    source_fields = type(source).model_fields.keys()
    target_fields = type(target).model_fields.keys()

    # Determine which fields to sync
    fields_to_sync = set(source_fields) & set(target_fields)

    # Apply default exclusions if enabled
    if exclude_defaults:
        # Default fields to exclude (even if they don't exist on the model)
        default_exclude = {"id", "created_at", "updated_at"}

        # Also exclude all foreign key fields (ending with _id)
        foreign_key_fields = {field for field in fields_to_sync if field.endswith("_id")}
        default_exclude.update(foreign_key_fields)

        exclude_fields = exclude_fields | default_exclude

    # Apply include_only filter if provided
    if include_only is not None:
        fields_to_sync &= include_only

    # Remove excluded fields
    fields_to_sync -= exclude_fields

    # Sync the fields
    for field_name in fields_to_sync:
        source_value = getattr(source, field_name, None)
        # Only set if the attribute exists and is not None to avoid overwriting defaults
        if source_value is not None or hasattr(target, field_name):
            setattr(target, field_name, source_value)
