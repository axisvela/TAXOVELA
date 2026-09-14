"""Plugin mechanism for ArchHarness extensions.

Enterprise overlays, connectors, and provider adapters extend the public
Core through this module — never by patching Core modules or copying Core
source. The dependency direction is permanent::

    plugin ──────> archharness (public Core)

A plugin is any object with three attributes::

    name            stable identifier, e.g. "enterprise"
    api_version     plugin API version it was built against, e.g. "1.2"
    capabilities    list of capability strings it provides, e.g.
                    ["policy.enforcement", "connector.servicenow"]

Discovery order:

1. entry points in group ``archharness.plugins`` (installed distributions);
2. in-process registrations via :func:`register_plugin` (tests, embedding).

Only plugins compatible with :data:`PLUGIN_API_VERSION` (same major
version) are accepted. Consumers gate enterprise surfaces on
:func:`has_capability`, never on ``try: import archharness_ee`` checks
scattered through Core code.

Domain-specific provider protocols (requirement readers, renderers,
connectors, rule packs) are added per domain on top of this mechanism.
"""

from __future__ import annotations

import unittest
from importlib import metadata

ENTRY_POINT_GROUP = "archharness.plugins"

PLUGIN_API_VERSION = "1.0"


class PluginError(ValueError):
    """Raised for malformed plugins or incompatible API versions."""


def _major(version: str) -> str:
    return str(version).split(".")[0]


def check_compatible(plugin: object) -> str:
    """Validate a plugin's shape and API version. Returns its name."""
    name = getattr(plugin, "name", None)
    api_version = getattr(plugin, "api_version", None)
    capabilities = getattr(plugin, "capabilities", None)
    if not name or not isinstance(name, str):
        raise PluginError("plugin must define a non-empty string `name`")
    if not api_version or not isinstance(api_version, str):
        raise PluginError(f"plugin {name!r} must define string `api_version`")
    if _major(api_version) != _major(PLUGIN_API_VERSION):
        raise PluginError(
            f"plugin {name!r} requires plugin API {api_version!r}, "
            f"Core provides {PLUGIN_API_VERSION!r}"
        )
    if not isinstance(capabilities, (list, tuple)) or not all(
        isinstance(cap, str) and cap for cap in capabilities
    ):
        raise PluginError(f"plugin {name!r} must define non-empty string `capabilities`")
    return name


_REGISTRY: dict[str, object] = {}


def register_plugin(plugin: object) -> object:
    """Register an in-process plugin after compatibility checks."""
    _REGISTRY[check_compatible(plugin)] = plugin
    return plugin


def unregister_plugin(name: str) -> None:
    """Remove an in-process registration (primarily for tests)."""
    _REGISTRY.pop(name, None)


def _entry_point_plugins() -> dict[str, object]:
    found: dict[str, object] = {}
    try:
        entry_points = metadata.entry_points(group=ENTRY_POINT_GROUP)
    except Exception:
        return found
    for entry_point in entry_points:
        try:
            plugin = entry_point.load()()
        except Exception:
            continue
        try:
            check_compatible(plugin)
        except PluginError:
            continue
        found[plugin.name] = plugin
    return found


def discover_plugins() -> dict[str, object]:
    """Return all compatible plugins: entry points overlaid with in-process ones."""
    discovered = _entry_point_plugins()
    discovered.update(_REGISTRY)
    return discovered


def capabilities() -> dict[str, list[str]]:
    """Map plugin name to its capability list."""
    return {name: list(plugin.capabilities) for name, plugin in discover_plugins().items()}


def has_capability(capability: str) -> bool:
    """Report whether any discovered plugin provides ``capability``."""
    return any(capability in caps for caps in capabilities().values())


class PluginContractTestCase(unittest.TestCase):
    """Contract kit for plugin authors. Subclass, opt into collection,
    and set ``plugin``::

        class TestEnterprisePlugin(PluginContractTestCase):
            __test__ = True  # required: the base opts out of collection
            plugin = enterprise_plugin

    Guarantees the plugin satisfies the Core loading contract so that a
    Core upgrade cannot silently break extension discovery.
    """

    __test__ = False  # base kit itself is not a test
    plugin: object = None

    def test_plugin_contract(self):
        self.assertIsNotNone(self.plugin, "contract test must set `plugin`")
        name = check_compatible(self.plugin)
        self.assertTrue(name)
        self.assertTrue(self.plugin.capabilities)
