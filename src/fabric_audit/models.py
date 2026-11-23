from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Device(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str = Field(min_length=1, description="The name of the device")
    role: Literal["leaf", "spine", "host"]


class Interface(BaseModel):
    model_config = ConfigDict(frozen=True)

    device: str = Field(min_length=1, description="Device the port is on, e.g. spine1")
    port: str = Field(min_length=1, description="Port on that device, e.g. eth1")


class Link(BaseModel):
    model_config = ConfigDict(frozen=True)

    interface_a: Interface
    interface_b: Interface

    @model_validator(mode="after")
    def different_devices(self):
        if self.interface_a.device == self.interface_b.device:
            raise ValueError("a link can't connect a device to itself")
        return self

    def key(self):
        """Return one value for this cable, whichever end is listed first.

        spine1:eth1 <-> leaf1:eth3 and leaf1:eth3 <-> spine1:eth1 get the same key.
        interface_a and interface_b stay exactly as reported.
        """
        end_a = (self.interface_a.device, self.interface_a.port)
        end_b = (self.interface_b.device, self.interface_b.port)

        # Smaller end first, so the order the ends came in doesn't matter
        if end_b < end_a:
            end_a, end_b = end_b, end_a

        return (end_a, end_b)
