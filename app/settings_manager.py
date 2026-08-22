class Setting:
    """Descriptor for a typed setting.

    The default is defined on the class.  An instance value is only stored
    after apply_settings() (or a direct assignment) overrides it.
    No file I/O — configuration arrives over WebSocket.
    """

    def __init__(self, default=None):
        self.default = default
        self.name = None

    def __set_name__(self, owner, name):
        self.name = name
        if not hasattr(owner, '_settings_fields'):
            owner._settings_fields = []
        owner._settings_fields.append(name)

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return instance.__dict__.get(self.name, self.default)

    def __set__(self, instance, value):
        instance.__dict__[self.name] = value


class SettingsManager:
    """Base class for settings holders.

    Subclasses declare settings as class-level Setting descriptors.
    Defaults are used until apply_settings() is called (typically from a
    WebSocket 'settings' message).
    """

    def apply_settings(self, data: dict) -> list:
        """Apply values from *data*, coercing each to the default's type.

        Returns the list of field names that were actually updated.
        Silently ignores unknown keys and type-incompatible values.
        """
        updated = []
        for name in getattr(self, '_settings_fields', []):
            if name not in data:
                continue
            descriptor = type(self).__dict__.get(name)
            if not isinstance(descriptor, Setting):
                continue
            raw = data[name]
            default = descriptor.default
            if default is not None:
                try:
                    raw = type(default)(raw)
                except (ValueError, TypeError):
                    continue
            setattr(self, name, raw)
            updated.append(name)
        return updated

    def get_settings(self) -> dict:
        """Return current values for all declared settings."""
        return {name: getattr(self, name) for name in getattr(self, '_settings_fields', [])}

    def reset_to_defaults(self):
        """Clear all instance-level overrides so class defaults take effect again."""
        for name in getattr(self, '_settings_fields', []):
            self.__dict__.pop(name, None)