from . import toposort
from .merge import SET_TYPES, Mergeable, merge, select_type


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
        if not isinstance(other, SET_TYPES):
            return NotImplemented
        return SetList(self | other)


class DAG(DefaultTags, Mergeable):
    def __init__(self, objsbykey, successors, prune_unreachable=None, required_keys=None):
        self.objsbykey = objsbykey
        self.successors = successors
        self.prune_unreachable = prune_unreachable
        self.required_keys = required_keys or {*[]}

    def merge(self, other):
        if not isinstance(other, DAG):
            return NotImplemented
        t = select_type(type(self), type(other), DAG)

        objsbykey = merge(self.objsbykey, other.objsbykey)
        successors = merge(self.successors, other.successors)
        prune_unreachable = merge(self.prune_unreachable, other.prune_unreachable, coallesce_none=True)
        required_keys = merge(self.required_keys, other.required_keys)

        return t(
            objsbykey=objsbykey,
            successors=successors,
            prune_unreachable=prune_unreachable,
            required_keys=required_keys,
        )

    def finalize_to_list(self, prune_unreachable=None):
        keys = sorted(self.objsbykey.keys())
        order, visible = toposort.order(keys, lambda k: sorted(self.successors.get(k, {*[]})))
        order.reverse()
        if prune_unreachable if prune_unreachable is not None else self.prune_unreachable:
            accessible = {*[]}
            for k in self.required_keys:
                accessible.update(visible[k])
            order = [k for k in order if k in accessible]
        return [self.objsbykey[k] for k in order]

    def __eq__(self, other) -> bool:
        if not isinstance(other, DAG):
            return NotImplemented
        return (
            self.objsbykey == other.objsbykey
            and self.successors == other.successors
            and self.prune_unreachable == other.prune_unreachable
            and self.required_keys == other.required_keys
        )

    @classmethod
    def to_yaml(cls, representer, node):
        return representer.represent_list(node.finalize_to_list())

    @classmethod
    def from_assoclist(cls, key, values):
        # encode key into the object id so that assoclists with different keys
        # do not interact with each in unexpected ways, they'll be treated as
        # separate nodes where the key value is identical.

        keys = [(key, v[key]) for v in values]
        successors = {k: {*keys[:i]} for i, k in enumerate(keys)}
        objsbykey = {(key, v[key]): v for v in values}
        # set required_keys to all for assoclists, but don't set prune_unreachable
        # so if merged with something that sets prune_unreachable, then nothing is pruned...
        return cls(objsbykey=objsbykey, successors=successors, required_keys={*keys})


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


class MergeMaps(DefaultTags, dict):
    yaml_tag = "!mergemap"

    @classmethod
    def to_yaml(cls, representer, node):
        return representer.represent_dict(dict(node))

    @classmethod
    def from_yaml(cls, constructor, node):
        maps = constructor.construct_sequence(node, deep=True)
        # just return plain dict, rather than subclass
        return {k: v for i in maps for k, v in i.items()}


class StrSet(DefaultTags, Mergeable, set):
    yaml_tag = "!stringset"

    @classmethod
    def from_yaml(cls, constructor, node):
        return cls(constructor.construct_sequence(node))

    @classmethod
    def to_yaml(cls, representer, node):
        x = [representer.represent_str(i).value for i in node]
        return representer.represent_scalar("tag:yaml.org,2002:str", "\n".join(x), style="|-")

    def merge(self, other):
        if not isinstance(other, SET_TYPES):
            return NotImplemented
        return StrSet(self | other)
