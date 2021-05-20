import argparse

from ruamel.yaml import YAML

from .merge import merge_all
from .template import template_list, template_props, template_repeat
from .toposort import apply_toposort


def prepend_notice(data):
    return "# generated file. do not edit directly\n" + data


def load_file(path: str, *, yaml=None):
    yaml = yaml or YAML()
    with open(path) as f:
        return yaml.load(f)


def dump_to_yaml(filename, data, *, yaml=None):
    yaml = yaml or YAML()
    with open(filename, "w") as f:
        yaml.dump(data, f, transform=prepend_notice)


def apply_single(components, output, files, *, loader=load_file, yaml=None):
    components = loader(components, yaml=yaml)
    data = [loader(p, yaml=yaml) for p in files]
    data = merge_all(data)
    step1 = apply_toposort(data)
    step2 = template_repeat(components, step1)
    step3 = template_list(components, step2)
    step4 = template_props(components, step3)
    return step4


def run(config, *, kont, files=None, apply=apply_single, yaml=None):
    if files is None:
        togen = config
    else:
        fset = set(files)
        togen = [i for i in config if i["output"] in fset or set(i["from"]) & fset]

    for item in togen:
        output = item["output"]
        components = item["components"]
        fromfiles = item["from"]

        print(f"generating {output}...")
        res = apply(components, output, fromfiles, yaml=yaml)
        kont(output, res, yaml=yaml)


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", "-c", required=False, default=".template-config.yaml")
    parser.add_argument("--only", "-o", action="store_true", default=False)
    parser.add_argument("files", nargs="*")
    args = parser.parse_args(argv)
    files = args.files
    only = args.only
    if not only:
        files = files or None

    config = load_file(args.config)
    yaml = YAML()
    run(config, files=files, kont=dump_to_yaml, yaml=yaml)


if __name__ == "__main__":
    main()
