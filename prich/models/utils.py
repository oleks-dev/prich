from prich.models.config import ConfigModel
from pydantic import BaseModel


def recursive_update(target: BaseModel, source: BaseModel) -> BaseModel:
    updated_data = {}

    for field in target.model_fields.keys():
        target_value = getattr(target, field)
        source_value = getattr(source, field)

        if source_value is None:
            updated_data[field] = target_value
        elif isinstance(target_value, dict) and isinstance(source_value, dict):
            updated_dict = dict(target_value)
            for k,v in source_value.items():
                if k not in updated_data.keys():
                    updated_dict[k] = v
                updated_data[field] = updated_dict
        elif isinstance(target_value, BaseModel) and isinstance(source_value, BaseModel):
            updated_data[field] = recursive_update(target_value, source_value)
        else:
            updated_data[field] = source_value

    return target.model_copy(update=updated_data)
