def select_type(left, right, other=None):
    if left is right or left == right:
        return right
    if issubclass(left, right):
        return left
    if issubclass(right, left):
        return right
    if other is None:
        raise TypeError("Cannot merge types")
    return other


def merge(left, right):
    if isinstance(left, dict):
        if isinstance(right, dict):
            t = select_type(type(left), type(right), dict)
            return t(
                {
                    **{k: (merge(left[k], right[k]) if k in right else left[k]) for k in left},
                    **{k: right[k] for k in right if k not in left},
                }
            )
        raise TypeError()
    if isinstance(left, list):
        if isinstance(right, list):
            t = select_type(type(left), type(right), list)
            ix = min(len(left), len(right))
            return t(
                [*[merge(l, r) for l, r in zip(left, right)], *[l for l in left[ix:]], *[r for r in right[ix:]],]
            )
        raise TypeError()
    if left == right:
        return left
    raise TypeError()


def merge_all(items):
    if not items:
        raise ValueError("Cannot merge no items")
    res = items[0]
    for i in items[1:]:
        res = merge(res, i)
    return res
