def apply_children(obj, func):
    if isinstance(obj, dict):
        return type(obj)(((k, func(v)) for k, v in obj.items()))
    elif isinstance(obj, list):
        return type(obj)([func(i) for i in obj])
    return obj
