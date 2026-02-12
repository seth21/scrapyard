# The "Phonebook"
NODE_REGISTRY = {}

def register_node(action_name):
    """
    Decorator to register an action class.
    Usage: @register_node("click")
    """
    def decorator(cls):
        NODE_REGISTRY[action_name] = cls
        return cls
    return decorator

def get_node_class(node_name):
    """Retrieves the class for a given action name."""
    node_cls = NODE_REGISTRY.get(node_name)
    if not node_cls:
        raise ValueError(f"Unknown action type: '{node_name}'. Available: {list(NODE_REGISTRY.keys())}")
    return node_cls