from .traverse import apply_children


def order(nodes, successors):
    visited = {*[]}
    visible = {}
    output = []

    def visit(n, root, onstack):
        v = {*[]}
        if n not in visited:
            visited.add(n)
            for i in successors(n):
                if i in onstack:
                    raise ValueError("Cycle in dependencies. participating nodes: {} -> {}".format(n, i))
                v = v | visit(i, root, onstack | {n})
            output.insert(0, n)
        visible[n] = visible.get(n, {*[]}) | v
        return visible[n] | {n}

    for i in nodes:
        visit(i, i, {*[]})

    return output, visible


def do_toposort(node, config):
    needs_key = config["deps_key"]
    required = set(config.get("required", []))
    strip_unrequired = config["strip_unreachable"]
    id_to_key = config["id_to_key"]

    def successors(key):
        try:
            needed = node[key].get(needs_key, [])
        except KeyError:
            raise KeyError(f"Key {key} missing in {node.keys()}")
        if isinstance(needed, str):
            return [needed]
        return needed or []

    def output_node(key):
        n = node[key]
        n.pop(needs_key, None)
        n.setdefault(id_to_key, key)
        return n

    def keep_node(key, visible):
        def isvisible(key):
            return any([key in visible[i] for i in required])

        if strip_unrequired:
            return key in required or isvisible(key)
        return True

    sorted, visible = order(node.keys(), successors)
    sorted.reverse()
    return [output_node(i) for i in sorted if keep_node(i, visible)]


def apply_toposort(obj):
    if not isinstance(obj, dict):
        return apply_children(obj, apply_toposort)

    config = obj.pop("__toposort", None)
    if config:
        new = do_toposort(obj, config)
        return [apply_children(i, apply_toposort) for i in new]
    return apply_children(obj, apply_toposort)
