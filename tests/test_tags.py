import io

import pytest

from avocado_config_gen import create_yaml, merge, tags


def _to_named_list(ls, key="name"):
    return [{key: i} for i in ls]


def test_dag_from_assoclist():
    a = tags.DAG.from_assoclist("name", _to_named_list([1, 2, 3, 4]))
    b = tags.DAG.from_assoclist("name", _to_named_list([1, 4, 5]))
    c = tags.DAG.from_assoclist("name", _to_named_list([0, 3, 5, 9]))
    x = merge.merge_all([a, b, c])
    assert x.finalize_to_list() == _to_named_list([0, 1, 2, 3, 4, 5, 9])
    # order should not matter...
    y = merge.merge_all([b, a, c])
    assert y.finalize_to_list() == _to_named_list([0, 1, 2, 3, 4, 5, 9])
    z = merge.merge_all([c, a, b])
    assert z.finalize_to_list() == _to_named_list([0, 1, 2, 3, 4, 5, 9])
    # serialisation to yaml should be stable...
    yaml = create_yaml()
    xbuf = io.StringIO()
    yaml.dump(x, xbuf)
    ybuf = io.StringIO()
    yaml.dump(y, ybuf)
    zbuf = io.StringIO()
    yaml.dump(z, zbuf)
    assert zbuf.getvalue() == ybuf.getvalue() == zbuf.getvalue()
    # and just to assert that the yaml is correct ...
    assert yaml.load(xbuf.getvalue()) == _to_named_list([0, 1, 2, 3, 4, 5, 9])


def test_dag_from_assoclist_cycle():
    a = tags.DAG.from_assoclist("name", _to_named_list([1, 2]))
    b = tags.DAG.from_assoclist("name", _to_named_list([2, 1]))
    c = merge.merge(a, b)
    with pytest.raises(ValueError):
        r = c.finalize_to_list()
        print("should not have returned:", r)


def test_named_assoc_list_deser():
    y = create_yaml()
    input = """
    !assocbyname
    - name: 1
    - name: 2
    - name: 3
    """

    d = y.load(input)
    assert d.finalize_to_list() == _to_named_list([1, 2, 3])


def test_id_assoc_list_deser():
    y = create_yaml()
    input = """
    !assocbyid
    - id: 1
    - id: 2
    - id: 3
    """

    d = y.load(input)
    assert d.finalize_to_list() == _to_named_list([1, 2, 3], key="id")
