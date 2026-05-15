"""Hostname resolution helpers for CLI commands."""

from collections.abc import Sequence
from dataclasses import dataclass

from paperctl.client.models import Entity


@dataclass(frozen=True)
class HostResolution:
    """Result of resolving user input against Host entities."""

    hostname: str | None
    was_partial: bool = False
    used_direct_fallback: bool = False
    ambiguous_matches: tuple[str, ...] = ()


def resolve_hostname_from_entities(system: str, entities: Sequence[Entity]) -> HostResolution:
    """Resolve a user-supplied system name against Host entities.

    SWO logs can contain hostnames even when the entities API returns no Host
    entities. In that case, keep the command usable by applying the requested
    system name directly as the host filter.
    """
    if not entities:
        return HostResolution(hostname=system, used_direct_fallback=True)

    exact = [e.name for e in entities if e.name == system]
    if exact:
        return HostResolution(hostname=exact[0])

    partial = [e.name for e in entities if system.lower() in e.name.lower()]
    if not partial:
        return HostResolution(hostname=None)

    if len(partial) == 1:
        return HostResolution(hostname=partial[0], was_partial=True)

    return HostResolution(hostname=None, ambiguous_matches=tuple(partial))
