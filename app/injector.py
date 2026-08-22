class Injector:
    _instances = {}

    @classmethod
    def put(cls, instance):
        cls._instances[type(instance)] = instance
        return instance  # allow chaining

    @classmethod
    def find(cls, cls_type):
        if cls_type not in cls._instances:
            # auto-create if not registered
            cls._instances[cls_type] = cls_type()
        return cls._instances[cls_type]

    @classmethod
    def clear(cls):
        cls._instances.clear()

def singleton(cls):
    """Decorator to auto-register a class as a singleton."""
    instance = cls()
    Injector.put(instance)
    return cls