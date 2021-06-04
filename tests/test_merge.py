import pytest

from avocado_config_gen.merge import Mergeable, merge


class Left(Mergeable, dict):
    def merge(self, other):
        return self


@pytest.mark.parametrize(
    ("input_a", "input_b", "expected"),
    [
        ({}, {}, {}),
        ({"a": 1}, {"a": 1}, {"a": 1}),
        ({"a": 1}, {"b": 2}, {"a": 1, "b": 2}),
        ({"a": {"b": 1}}, {"a": {"c": 2}}, {"a": {"b": 1, "c": 2}}),
        ("a", "a", "a"),
        ([], [], []),
        ([1], [1], [1]),
        (1, 1, 1),
        # Left is strictly invalid, but it should work if only on one side
        (Left({"foo": "a"}), "b", Left({"foo": "a"})),
        ("a", Left({"foo": "b"}), Left({"foo": "b"})),
    ],
)
def test_merge(input_a, input_b, expected):
    res = merge(input_a, input_b)
    assert res == expected
    # commutative
    assert res == merge(input_b, input_a)
    # idempotent
    assert res == merge(res, expected)
    assert res == merge(res, input_a)
    assert res == merge(res, input_b)


@pytest.mark.parametrize(
    ("input_a", "input_b"),
    [
        ({"a": 1}, {"a": 2}),
        (1, 2),
        ("a", "b"),
        (
            [
                1,
            ],
            [
                2,
            ],
        ),
        (Left({"foo": "bar"}), Left({"foo": "baz"})),
        # without coalesce none, these fail:
        (1, None),
        (None, "foo"),
    ],
)
def test_merge_error(input_a, input_b):
    with pytest.raises(TypeError):
        merge(input_a, input_b)


def test_merge_coallesce_none():
    assert merge(1, None, coallesce_none=True) == 1
    assert merge(None, 1, coallesce_none=True) == 1
