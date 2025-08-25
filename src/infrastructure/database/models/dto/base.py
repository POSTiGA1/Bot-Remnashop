from typing import Any

from pydantic import BaseModel as _BaseModel
from pydantic import ConfigDict, PrivateAttr


class PydanticModel(_BaseModel):
    model_config = ConfigDict(
        extra="ignore",
        from_attributes=True,
        populate_by_name=True,
    )


class TrackableModel(PydanticModel):
    __changed_data: dict[str, Any] = PrivateAttr(default_factory=dict)

    @property
    def changed_data(self) -> dict[str, Any]:
        return self.__changed_data

    def __setattr__(self, name: str, value: Any) -> None:
        super().__setattr__(name, value)
        self.__changed_data[name] = value
