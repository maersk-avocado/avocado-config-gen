import pytest

from avocado_config_gen.toposort import do_toposort, order


@pytest.mark.parametrize(
    ("input", "exporder", "expvisible"),
    [
        ({1: [2], 2: [3], 3: []}, [1, 2, 3], {1: {2, 3}, 2: {3}, 3: {*[]}}),
        (
            {1: [2], 2: [3], 3: [], 4: [5], 5: [2]},
            [4, 5, 1, 2, 3],
            {1: {2, 3}, 2: {3}, 3: {*[]}, 4: {5, 2, 3}, 5: {2, 3}},
        ),
        ({1: [], 2: [], 3: []}, [3, 2, 1], {1: {*[]}, 2: {*[]}, 3: {*[]}}),
    ],
)
def test_order(input, exporder, expvisible):
    res = order(input.keys(), input.get)
    assert res[0] == exporder
    assert res[1] == expvisible


@pytest.mark.parametrize(
    ("input",),
    [
        ({1: [2], 2: [1]},),
        ({1: [2], 2: [3], 3: [1]},),
    ],
)
def test_cycles(input):
    with pytest.raises(ValueError):
        order(input.keys(), input.get)


def test_do_toposort():
    input = {
        "a": {"__needs": "b"},
        "b": {"__needs": ["c", "d"]},
        "c": {},
        "d": {"__needs": ["c"]},
        "e": {"__needs": ["b"]},
        "f": {},
    }
    config = {
        "deps_key": "__needs",
        "strip_unreachable": True,
        "required": ["a"],
        "id_to_key": "id",
    }
    res = do_toposort(input, config)
    ids = [i["id"] for i in res]
    assert ids == ["c", "d", "b", "a"]
