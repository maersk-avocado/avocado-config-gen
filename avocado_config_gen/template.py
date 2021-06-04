import re

from .traverse import apply_children


def template_repeat(items, obj):
    def go(obj):
        if not isinstance(obj, list):
            return apply_children(obj, go)
        return type(obj)([j for i in obj for j in apply(i)])

    def apply(obj):
        if not isinstance(obj, dict):
            return [go(obj)]
        config = obj.pop("__template_repeat", None)
        if config:
            to_apply = filter_items(items, config)
            return [apply_template(i, obj) for i in to_apply]
        return [go(obj)]

    return go(obj)


def template_list(items, obj):
    def go(obj):
        if not isinstance(obj, dict):
            return apply_children(obj, go)
        config = obj.pop("__template_list", None)
        if config:
            insert_key = config["insert_key"]
            insert_val = config["insert_val"]
            to_apply = filter_items(items, config)
            return type(obj)({**obj, insert_key: [apply_template(i, insert_val) for i in to_apply]})
        return apply_children(obj, go)

    return go(obj)


def template_props(items, obj):
    def go(obj):
        if not isinstance(obj, dict):
            return apply_children(obj, go)
        config = obj.pop("__template_props", None)
        cl = config_list(config)
        if cl:
            return type(obj)(
                {
                    **obj,
                    **{
                        apply_template(i, config["insert_key"]): apply_template(i, config["insert_val"])
                        for config in cl
                        for i in filter_items(items, config)
                    },
                }
            )
        return apply_children(obj, go)

    return go(obj)


def config_list(config):
    if not config:
        return None
    if isinstance(config, dict):
        return [config]
    if isinstance(config, list):
        return config
    raise TypeError(f"unexpected type {type(config)}")


def filter_items(items, obj):
    if isinstance(obj, dict):
        filter = obj.get("filter", None)
        if filter:
            key = filter["key"]
            match = filter["match"]
            regex = re.compile(match)
            return [i for i in items if regex.match(i[key])]
    elif not isinstance(obj, bool):
        raise TypeError(f"Unexpected type for obj: {type(obj)}")
    return items


def apply_template(templ, obj):
    def go(obj):
        if isinstance(obj, str):
            return type(obj)(obj % templ)
        elif isinstance(obj, dict):
            return type(obj)({go(k): go(v) for k, v in obj.items()})
        return apply_children(obj, go)

    return go(obj)
