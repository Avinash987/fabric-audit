from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Device(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str = Field(min_length=1, description="The name of the device")
    role: Literal["leaf", "spine", "host"]


class Interface(BaseModel):
    model_config = ConfigDict(frozen=True)

    device_name: str = Field(
        min_length=1,
        description="The name of the device to which the interface belongs",
    )
    name: str = Field(min_length=1, description="The name of the interface")

    def sort_key(self) -> tuple[str, str]:
        return (self.device_name, self.name)


class Link(BaseModel):
    """One expected cable. A->B and B->A are stored the same way."""

    model_config = ConfigDict(frozen=True)

    interface_a: Interface
    interface_b: Interface

    @model_validator(mode="before")
    @classmethod
    def order_ends(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        if "interface_a" not in data or "interface_b" not in data:
            return data  # let Pydantic report the missing field
        a = Interface.model_validate(data["interface_a"])
        b = Interface.model_validate(data["interface_b"])
        if b.sort_key() < a.sort_key():
            a, b = b, a
        return {**data, "interface_a": a, "interface_b": b}

    @model_validator(mode="after")
    def different_devices(self) -> "Link":
        if self.interface_a.device_name == self.interface_b.device_name:
            raise ValueError(f"link connects {self.interface_a.device_name} to itself")
        return self
