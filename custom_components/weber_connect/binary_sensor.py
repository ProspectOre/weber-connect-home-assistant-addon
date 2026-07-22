"""Native connection context for Weber Connect."""

from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import WeberCoordinator
from .entity import WeberEntity
from .models import WeberRuntimeData


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the connection context entity."""

    runtime: WeberRuntimeData = entry.runtime_data
    async_add_entities([WeberConnectionBinarySensor(runtime.coordinator, entry)])


class WeberConnectionBinarySensor(WeberEntity, BinarySensorEntity):
    """Report whether Home Assistant is receiving fresh hub data."""

    _attr_translation_key = "connection"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    def __init__(self, coordinator: WeberCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, "connection")

    @property
    def is_on(self) -> bool:
        """Return whether the selected transport is receiving hub data."""

        return bool(self.coordinator.data.get("connected", False))

    @property
    def available(self) -> bool:
        """Keep connection context visible while the hub is offline."""

        return True

    @property
    def icon(self) -> str:
        """Show both the configured transport and its current state."""

        connected = self.is_on
        if self.coordinator.data.get("source") == "cloud":
            return "mdi:cloud-check-outline" if connected else "mdi:cloud-off-outline"
        return "mdi:bluetooth-connect" if connected else "mdi:bluetooth-off"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose the human-readable transport used by this entry."""

        source = self.coordinator.data.get("source")
        return {
            "connection_method": "Weber Cloud" if source == "cloud" else "Bluetooth",
        }
