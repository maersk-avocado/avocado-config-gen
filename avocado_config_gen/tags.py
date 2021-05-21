from .merge import Mergeable


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
