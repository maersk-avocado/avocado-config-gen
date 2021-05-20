import pytest

from avocado_config_gen.merge import merge


@pytest.mark.parametrize(
    ("input_a", "input_b", "expected"),
    [
        ({}, {}, {}),
        ({"a": 1}, {"a": 1}, {"a": 1}),
        ({"a": 1}, {"b": 2}, {"a": 1, "b": 2}),
        ({"a": {"b": 1}}, {"a": {"c": 2}}, {"a": {"b": 1, "c": 2}}),
        ("a", "a", "a"),
        (1, 1, 1),
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
    ],
)
def test_merge_error(input_a, input_b):
    with pytest.raises(TypeError):
        merge(input_a, input_b)
