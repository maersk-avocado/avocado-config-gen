import pytest

from avocado_config_gen.template import apply_template, template_list, template_props, template_repeat


@pytest.mark.parametrize(
    ("tpl", "obj", "expected"),
    [
        ({"hello": "world"}, "hello, %(hello)s!", "hello, world!"),
        ({"hello": "world"}, {"message to %(hello)s": "hello, %(hello)s!"}, {"message to world": "hello, world!"}),
        ({"ex": "ABC"}, ["(%(ex)s)", {"foo": "%(ex)s"}, ["%(ex)s"]], ["(ABC)", {"foo": "ABC"}, ["ABC"]]),
    ],
)
def test_apply_template(tpl, obj, expected):
    res = apply_template(tpl, obj)
    assert res == expected


@pytest.mark.parametrize(
    ("config", "include"),
    [
        (True, "abc"),
        ({"filter": {"key": "meta", "match": "^y"}}, "ac"),
        ({"filter": {"key": "meta", "match": "^n"}}, "b"),
        ({"filter": {"key": "meta", "match": "^NOMATCH$"}}, ""),
    ],
)
def test_template_repeat(config, include):
    input = [
        {
            "id": "foo",
        },
        {"__template_repeat": config, "id": "test_%(item)s", "inner": {"vals": ["%(val)s"]}},
        {"id": "bar"},
    ]
    components = [
        {"item": "a", "val": "A", "meta": "yes, sir"},
        {"item": "b", "val": "B", "meta": "no"},
        {"item": "c", "val": "C", "meta": "yes"},
    ]
    res = template_repeat(components, input)
    assert res == [
        {"id": "foo"},
        *([{"id": "test_a", "inner": {"vals": ["A"]}}] if "a" in include else []),
        *([{"id": "test_b", "inner": {"vals": ["B"]}}] if "b" in include else []),
        *([{"id": "test_c", "inner": {"vals": ["C"]}}] if "c" in include else []),
        {"id": "bar"},
    ]


@pytest.mark.parametrize(
    ("insert_val", "expected"),
    [
        ("%(id)s", ["a", "b", "c"]),
        ({"v": "%(id)s"}, [{"v": "a"}, {"v": "b"}, {"v": "c"}]),
    ],
)
def test_template_list(insert_val, expected):
    input = {
        "__template_list": {
            "insert_key": "foo",
            "insert_val": insert_val,
        },
        "bar": "hello",
    }
    components = [
        {"id": "a"},
        {"id": "b"},
        {"id": "c"},
    ]
    res = template_list(components, input)
    assert res == {"foo": expected, "bar": "hello"}


@pytest.mark.parametrize(
    ("insert_val", "expected"),
    [
        ("%(val)s", {"test_a": "A", "test_b": "B", "test_c": "C"}),
    ],
)
def test_template_props(insert_val, expected):
    input = {
        "__template_props": {"insert_key": "test_%(key)s", "insert_val": insert_val},
        "foo": 1,
        "bar": 2,
    }
    components = [
        {"key": "a", "val": "A"},
        {"key": "b", "val": "B"},
        {"key": "c", "val": "C"},
    ]
    res = template_props(components, input)
    assert res == dict({"foo": 1, "bar": 2}, **expected)
