"""Tests for CLI hostname resolution."""

from paperctl.cli.hosts import resolve_hostname_from_entities
from paperctl.client.models import Entity


def host(name: str) -> Entity:
    return Entity(id=name, type="Host", name=name)


def test_resolve_hostname_exact_match() -> None:
    resolution = resolve_hostname_from_entities(
        "web-1.example.com",
        [host("web-1.example.com"), host("web-2.example.com")],
    )

    assert resolution.hostname == "web-1.example.com"
    assert resolution.was_partial is False
    assert resolution.used_direct_fallback is False


def test_resolve_hostname_partial_match() -> None:
    resolution = resolve_hostname_from_entities(
        "web-1",
        [host("web-1.example.com"), host("web-2.example.com")],
    )

    assert resolution.hostname == "web-1.example.com"
    assert resolution.was_partial is True


def test_resolve_hostname_ambiguous_partial_match() -> None:
    resolution = resolve_hostname_from_entities(
        "web",
        [host("web-1.example.com"), host("web-2.example.com")],
    )

    assert resolution.hostname is None
    assert resolution.ambiguous_matches == ("web-1.example.com", "web-2.example.com")


def test_resolve_hostname_missing_match() -> None:
    resolution = resolve_hostname_from_entities("db-1", [host("web-1.example.com")])

    assert resolution.hostname is None
    assert resolution.used_direct_fallback is False


def test_resolve_hostname_falls_back_when_no_host_entities() -> None:
    resolution = resolve_hostname_from_entities("nuc13-142", [])

    assert resolution.hostname == "nuc13-142"
    assert resolution.used_direct_fallback is True
