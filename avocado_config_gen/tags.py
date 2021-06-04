from . import toposort
from .merge import Mergeable, merge, select_type


class DefaultTags:
    _subclasses = []

    def __init_subclass__(cls) -> None:
        DefaultTags._subclasses.append(cls)


class SetList(DefaultTags, Mergeable, set):
    yaml_tag = "!set"

    @classmethod
    def from_yaml(cls, constructor, node):
        return cls(constructor.construct_sequence(node))

    @classmethod
    def to_yaml(cls, representer, node):
        # when we serialise the set, we want to serialise as a normal list.
        # we just care about the set property for merging
        # order is sorted so that it is a deterministic output
        return representer.represent_list(sorted(node))

    def merge(self, other):
        if not isinstance(other, set):
            return NotImplemented
        return SetList(self | other)


class DAG(DefaultTags, Mergeable):
    def __init__(self, objsbykey, successors):
        self.objsbykey = objsbykey
        self.successors = successors

    def merge(self, other):
        if not isinstance(other, DAG):
            return NotImplemented
        t = select_type(type(self), type(other), DAG)

        objsbykey = merge(self.objsbykey, other.objsbykey)
        successors = merge(self.successors, other.successors)

        return t(objsbykey=objsbykey, successors=successors)

    def finalize_to_list(self):
        keys = sorted(self.objsbykey.keys())
        order, _ = toposort.order(keys, lambda k: sorted(self.successors.get(k, {*[]})))
        order.reverse()
        return [self.objsbykey[k] for k in order]

    def __eq__(self, other) -> bool:
        if not isinstance(other, DAG):
            return NotImplemented
        return self.objsbykey == other.objsbykey and self.successors == other.successors

    @classmethod
    def to_yaml(cls, representer, node):
        return representer.represent_list(node.finalize_to_list())

    @classmethod
    def from_assoclist(cls, key, values):
        keys = [(key, v[key]) for v in values]
        successors = {k: {*keys[:i]} for i, k in enumerate(keys)}
        objsbykey = {(key, v[key]): v for v in values}
        return cls(objsbykey=objsbykey, successors=successors)


class NamedAssocList(DAG, DefaultTags):
    yaml_tag = "!assocbyname"

    @classmethod
    def from_yaml(cls, constructor, node):
        return cls.from_assoclist("name", constructor.construct_sequence(node, deep=True))


class IdAssocList(DAG, DefaultTags):
    yaml_tag = "!assocbyid"

    @classmethod
    def from_yaml(cls, constructor, node):
        return cls.from_assoclist("id", constructor.construct_sequence(node, deep=True))
