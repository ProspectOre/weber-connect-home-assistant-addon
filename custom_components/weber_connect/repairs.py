"""Actionable Home Assistant repairs for Weber Connect Unofficial."""

from __future__ import annotations

import voluptuous as vol
from homeassistant.components.repairs import RepairsFlow, RepairsFlowResult
from homeassistant.core import HomeAssistant

from .models import WeberRuntimeData


class ConnectionRepairFlow(RepairsFlow):
    """Retry a hub connection and report whether data resumed."""

    def __init__(self, entry_id: str) -> None:
        self._entry_id = entry_id

    async def async_step_init(self, user_input: dict[str, str] | None = None) -> RepairsFlowResult:
        return await self.async_step_confirm(user_input)

    async def async_step_confirm(
        self, user_input: dict[str, str] | None = None
    ) -> RepairsFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            entry = self.hass.config_entries.async_get_entry(self._entry_id)
            if entry is None:
                return self.async_create_entry(data={})
            runtime = getattr(entry, "runtime_data", None)
            if not isinstance(runtime, WeberRuntimeData):
                errors["base"] = "entry_not_loaded"
                return self.async_show_form(
                    step_id="confirm",
                    data_schema=vol.Schema({}),
                    errors=errors,
                )
            if await runtime.coordinator.async_retry():
                return self.async_create_entry(data={})
            errors["base"] = "still_unavailable"
        return self.async_show_form(
            step_id="confirm",
            data_schema=vol.Schema({}),
            errors=errors,
        )


class CredentialRepairFlow(RepairsFlow):
    """Remove a rejected generated companion so it can be paired again."""

    def __init__(self, entry_id: str) -> None:
        self._entry_id = entry_id

    async def async_step_init(self, user_input: dict[str, str] | None = None) -> RepairsFlowResult:
        return await self.async_step_confirm(user_input)

    async def async_step_confirm(
        self, user_input: dict[str, str] | None = None
    ) -> RepairsFlowResult:
        if user_input is not None:
            if self.hass.config_entries.async_get_entry(self._entry_id) is not None:
                await self.hass.config_entries.async_remove(self._entry_id)
            return self.async_create_entry(data={})
        return self.async_show_form(step_id="confirm", data_schema=vol.Schema({}))


async def async_create_fix_flow(
    hass: HomeAssistant,
    issue_id: str,
    data: dict[str, str | int | float | None] | None,
) -> RepairsFlow:
    """Create a retry flow for a sustained connection failure."""

    entry_id = data.get("entry_id") if data is not None else None
    if not isinstance(entry_id, str):
        raise ValueError(f"Repair {issue_id} is missing its config entry.")
    if issue_id.startswith("credentials_rejected_"):
        return CredentialRepairFlow(entry_id)
    return ConnectionRepairFlow(entry_id)
