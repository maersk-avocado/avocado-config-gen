import abc
from collections import abc as colabc

SET_TYPES = (
    set,
    colabc.MutableSet,
    colabc.Set,
)


class NonCommutativeMergeError(TypeError):
    pass


class NonMergeableTypesError(TypeError):
    pass


class Mergeable(abc.ABC):
    @abc.abstractmethod
    def merge(self, other):
        ...

    def rmerge(self, other):
        return self.merge(other)


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


def merge(left, right, coallesce_none=False):
    x = 0
    if isinstance(left, Mergeable):
        res = left.merge(right)
        if res is not NotImplemented:
            left = res
            x = x | 1
    # if isinstance(right, Mergeable) and type(left) is not type(right):
    if isinstance(right, Mergeable):
        res = right.rmerge(left)
        if res is not NotImplemented:
            right = res
            x = x | 2
    if x == 1:
        return left
    elif x == 2:
        return right
    elif x == 3:
        # both left and right were Mergeable
        # assert that both were commutable together by asserting equal output
        if left == right:
            return left
        raise NonCommutativeMergeError("Merging operations are non-commutable!")

    if isinstance(left, dict):
        if isinstance(right, dict):
            t = select_type(type(left), type(right), dict)
            return t(
                (
                    *((k, (merge(left[k], right[k])) if k in right else left[k]) for k in left),
                    *((k, right[k]) for k in right if k not in left),
                )
            )
        raise NonMergeableTypesError(f"Cannot merge dict and {type(right)}")
    if isinstance(left, SET_TYPES):
        if isinstance(right, SET_TYPES):
            t = select_type(type(left), type(right), set)
            return t(left | right)
        raise NonMergeableTypesError(f"Cannot merge set and {type(right)}")
    # do not automatically merge lists
    # cue behaviour is to do an elementwise merge as implemented
    # in commented section below. we shall not do this and rely
    # on merging strategies via tags
    # if isinstance(left, list):
    #    if isinstance(right, list):
    #        t = select_type(type(left), type(right), list)
    #        ix = min(len(left), len(right))
    #        return t(
    #            [
    #                *[merge(i, j) for i, j in zip(left, right)],
    #                *[i for i in left[ix:]],
    #                *[j for j in right[ix:]],
    #            ]
    #        )
    #    raise TypeError()
    if left == right:
        return left
    if coallesce_none:
        if left is None:
            return right
        if right is None:
            return left
    raise NonMergeableTypesError(f"Cannot merge {type(left)} and {type(right)} or values conflict")


def merge_all(items):
    if not items:
        raise ValueError("Cannot merge no items")
    res = items[0]
    for i in items[1:]:
        res = merge(res, i)
    return res
