import pytest
from mockify import satisfied
from mockify.actions import Return
from mockify.mock import Mock

from avocado_config_gen import run


@pytest.mark.parametrize(
    ("files", "expected"),
    [
        (None, [0, 1]),
        (["output1.yaml"], [0]),
        (["output2.yaml"], [1]),
        (["output1.yaml", "output2.yaml"], [0, 1]),
        (["output1.yaml", "input_a.yaml"], [0, 1]),
        (["output1.yaml", "input_2.yaml"], [0]),
        (["input_2.yaml", "input_3.yaml"], [0]),
        (["input_1.yaml", "input_c.yaml"], [0, 1]),
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
        run(config, kont=kont, files=files and set(files), apply=apply)
