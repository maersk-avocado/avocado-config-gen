import pytest
from mockify import satisfied
from mockify.actions import Return
from mockify.mock import Mock

from avocado_config_gen import all_files, combined_loader, run


class File(str):
    ...


@pytest.mark.parametrize(
    ("files", "expected"),
    [
        (None, [0, 1]),
        ({"output1.yaml"}, [0]),
        ({"output2.yaml"}, [1]),
        ({"output1.yaml", "output2.yaml"}, [0, 1]),
        ({"output1.yaml", "input_a.yaml"}, [0, 1]),
        ({"output1.yaml", "input_2.yaml"}, [0]),
        ({"input_2.yaml", "input_3.yaml"}, [0]),
        ({"input_1.yaml", "input_c.yaml"}, [0, 1]),
        ({"foo.yaml"}, [0, 1]),
        # unrelated files should trigger no applications:
        ({"bar.yaml", "qux.yaml"}, []),
    ],
)
def test_run(files, expected):
    kont = Mock("kont")
    apply = Mock("apply")

    config = [
        {
            "output": "output1.yaml",
            "components": "foo.yaml",
            "from": ["input_1.yaml", "input_2.yaml", "input_3.yaml"],
        },
        {
            "output": "output2.yaml",
            "components": "foo.yaml",
            "from": ["input_a.yaml", "input_b.yaml", "input_c.yaml"],
        },
    ]

    for i in expected:
        data = config[i]
        apply.expect_call(data["components"], data["output"], data["from"], yaml=None).will_once(Return(i))
        kont.expect_call(data["output"], i, yaml=None).will_once(Return(None))

    with satisfied(kont, apply):
        run(config, kont=kont, files=files, apply=apply)


@pytest.mark.parametrize(
    ["config", "expected"],
    [
        ("/path/to/file.yaml", File("/path/to/file.yaml")),
        ({"path": "/path/to/file.yaml"}, File("/path/to/file.yaml")),
        ({"path": "/path/to/file.yaml", "prefix_at": "a/b/c"}, {"a": {"b": {"c": File("/path/to/file.yaml")}}}),
        ({"value": ["test"]}, ["test"]),
        ({"value": ["test"], "prefix_at": "a"}, {"a": ["test"]}),
        ({"yaml": '"key": 3\n'}, {"key": 3}),
        (
            {"value": {"a": {"b": {"c": 999}}}, "extract_from": "a/b/c", "prefix_at": "hello/world"},
            {"hello": {"world": 999}},
        ),
    ],
)
def test_combined_loader(config, expected):
    result = combined_loader(config, file_loader=lambda f, **k: File(f))
    assert expected == result


def test_all_files():
    data = [
        "/path/to/file.yaml",
        {"path": "/another/file.yaml"},
        {},
        {"value": "some value"},
        {"yaml": '"some yaml"'},
    ]
    assert all_files(data) == {"/path/to/file.yaml", "/another/file.yaml"}
