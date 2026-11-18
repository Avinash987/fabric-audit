from typing import Literal

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


class Link(BaseModel):
    model_config = ConfigDict(frozen=True)

    interface_a: Interface
    interface_b: Interface

    @model_validator(mode="after")
    def different_devices(self):
        if self.interface_a.device_name == self.interface_b.device_name:
            raise ValueError("a link can't connect a device to itself")
        return self

    def key(self):
        # Same key for A->B and B->A, so both directions count as one cable
        ends = [
            (self.interface_a.device_name, self.interface_a.name),
            (self.interface_b.device_name, self.interface_b.name),
        ]
        return tuple(sorted(ends))
