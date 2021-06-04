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


class AssocList(DefaultTags, Mergeable):
    def __init__(self, key, keys, objs, orders):
        self.key = key
        self.keys = keys
        self.objs = objs
        self.orders = orders

    @classmethod
    def from_assoclist(cls, id_, key, values):
        key = key
        keys = {v[key]: {id_: i} for i, v in enumerate(values)}
        objs = {v[key]: v for v in values}
        orders = {id_: [v[key] for v in values]}
        return cls(key, keys, objs, orders)

    def merge(self, other):
        if not isinstance(other, AssocList):
            if isinstance(other, list):
                other = AssocList.from_assoclist(self.key, other)
            else:
                return NotImplemented

        key = merge(self.key, other.key)
        keys = merge(self.keys, other.keys)
        objs = merge(self.objs, other.objs)
        orders = merge(self.orders, other.orders)
        return select_type(type(self), type(other))(key, keys, objs, orders)

    def _successors_for_key(self, key):
        successors = {*[]}
        for k, v in self.keys.get(key, {}).items():
            successors.update(self.orders[k][:v])
        return sorted(successors)

    def finalize_to_list(self):
        order, _ = toposort.order(sorted(self.objs.keys()), self._successors_for_key)
        order.reverse()
        return [self.objs[i] for i in order]

    def __eq__(self, other) -> bool:
        if not isinstance(other, AssocList):
            return NotImplemented
        return (
            self.key == other.key
            and self.keys == other.keys
            and self.objs == other.objs
            and self.orders == other.orders
        )

    @classmethod
    def to_yaml(cls, representer, node):
        return representer.represent_list(node.finalize_to_list())


class NamedAssocList(AssocList, DefaultTags):
    yaml_tag = "!assocbyname"

    @classmethod
    def from_yaml(cls, constructor, node):
        return cls.from_assoclist(id(node), "name", constructor.construct_sequence(node, deep=True))


class IdAssocList(AssocList, DefaultTags):
    yaml_tag = "!assocbyid"

    @classmethod
    def from_yaml(cls, constructor, node):
        return cls.from_assoclist(id(node), "id", constructor.construct_sequence(node, deep=True))
