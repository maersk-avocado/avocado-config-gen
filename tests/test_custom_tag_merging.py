import io

from avocado_config_gen import create_yaml
from avocado_config_gen.merge import merge


def test_set_merge_and_output():
    yaml = create_yaml()

    data_l = yaml.load(
        """
    foo: !set
    - a
    """
    )
    assert data_l == {"foo": {"a"}}

    data_r = yaml.load(
        """
    foo: !set
    - b
    """
    )
    assert data_r == {"foo": {"b"}}

    merged = merge(data_l, data_r)
    assert merged == {"foo": {"a", "b"}}

    # when outputting it should be output as a normal list
    buf = io.StringIO()
    yaml.dump(merged, buf)
    reparsed = yaml.load(buf.getvalue())
    # output is ordered when dumping to be deterministic:
    assert reparsed["foo"] == ["a", "b"]
    assert isinstance(reparsed["foo"], list)


def test_set_merge_with_yaml_set():
    yaml = create_yaml()

    data_l = yaml.load(
        """
    foo: !set
    - a
    - b
    - c
    """
    )

    data_r = yaml.load(
        """
    foo: !!set
      ? a
      ? d
      ? b
    """
    )

    merged = merge(data_l, data_r)
    assert merged == {"foo": {"a", "b", "c", "d"}}

    # identical merge in reverse
    merged_op = merge(data_r, data_l)
    assert merged_op == {"foo": {"a", "b", "c", "d"}}

    # when outputting it should be output as a normal list
    buf = io.StringIO()
    yaml.dump(merged, buf)
    reparsed = yaml.load(buf.getvalue())
    # output is ordered when dumping to be deterministic:
    assert reparsed["foo"] == ["a", "b", "c", "d"]
    assert isinstance(reparsed["foo"], list)
