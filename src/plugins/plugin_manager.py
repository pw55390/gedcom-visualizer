"""
Pluggy Plugin Architecture Manager.
Provides extensible hook specifications for third-party extensions.
"""

import pluggy

hookspec = pluggy.HookspecMarker("genealogy_enterprise")
hookimpl = pluggy.HookimplMarker("genealogy_enterprise")


class PluginSpecs:
    """Plugin hook specifications for extension developers."""

    @hookspec
    def on_person_created(self, person_id: str, full_name: str) -> None:
        """Called whenever a new person is created in the database."""

    @hookspec
    def custom_validation_rule(self, person_id: str) -> str:
        """Allows plugins to return custom validation issue messages."""


class PluginManager:
    def __init__(self):
        self.pm = pluggy.PluginManager("genealogy_enterprise")
        self.pm.add_hookspecs(PluginSpecs)

    def register_plugin(self, plugin_instance):
        """Registers a plugin instance."""
        self.pm.register(plugin_instance)

    def notify_person_created(self, person_id: str, full_name: str):
        self.pm.hook.on_person_created(person_id=person_id, full_name=full_name)

    def run_custom_validations(self, person_id: str):
        return self.pm.hook.custom_validation_rule(person_id=person_id)
