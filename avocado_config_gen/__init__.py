import argparse
from typing import List, Optional, Set, Tuple

from ruamel.yaml import YAML

from .merge import merge_all
from .tags import DefaultTags
from .template import template_list, template_props, template_repeat
from .toposort import apply_toposort


def create_yaml():
    yaml = YAML()
    for cls in DefaultTags._subclasses:
        yaml.register_class(cls)
    return yaml


def prepend_notice(data):
    return "# generated file. do not edit directly\n" + data


def load_file(path: str, *, yaml=None):
    yaml = yaml or create_yaml()
    with open(path) as f:
        return yaml.load(f)


def path_from_config(config) -> Tuple[Optional[str], dict]:
    if isinstance(config, str):
        return config, {}
    elif isinstance(config, dict):
        if "path" in config:
            return config["path"], config
    else:
        raise TypeError(f"Unexpected config type: {type(config)}")
    return None, config


def combined_loader(config, *, yaml=None, file_loader=load_file):
    yaml = yaml or create_yaml()
    path, config = path_from_config(config)
    if path is not None:
        data = file_loader(path, yaml=yaml)
    elif "value" in config:
        data = config["value"]
    elif "yaml" in config:
        data = yaml.load(config["yaml"])

    if "prefix_at" in config:
        prefix_path = config["prefix_at"].split("/")
        while prefix_path:
            cur = prefix_path.pop()
            data = {cur: data}

    return data


def dump_to_yaml(filename, data, *, yaml=None):
    yaml = yaml or create_yaml()
    with open(filename, "w") as f:
        yaml.dump(data, f, transform=prepend_notice)


def apply_single(components, output: str, files: List[str], *, loader=combined_loader, yaml: Optional[YAML] = None):
    components = loader(components, yaml=yaml)
    data = [loader(p, yaml=yaml) for p in files]
    data = merge_all(data)
    step1 = apply_toposort(data)
    step2 = template_repeat(components, step1)
    step3 = template_list(components, step2)
    step4 = template_props(components, step3)
    return step4


def all_files(from_) -> Set[str]:
    return {p[0] for p in map(path_from_config, from_) if p[0] is not None}


def run(
    config,
    *,
    kont,
    files: Optional[Set[str]] = None,
    apply=apply_single,
    yaml: Optional[YAML] = None,
    config_changed: bool = False,
):
    if files is None or config_changed:
        togen = config
    else:
        togen = [
            i
            for i in config
            if (i["output"] in files) or (i["components"] in files) or (all_files(i["from"]) & files)
        ]

    for item in togen:
        output = item["output"]
        components = item["components"]
        fromfiles = item["from"]

        print(f"generating {output}...")
        res = apply(components, output, fromfiles, yaml=yaml)
        kont(output, res, yaml=yaml)


def main(argv: Optional[List[str]] = None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", "-c", required=False, default=".template-config.yaml")
    parser.add_argument("--only", "-o", action="store_true", default=False)
    parser.add_argument("files", nargs="*")
    args = parser.parse_args(argv)
    files = set(args.files)
    only = args.only
    if not only:
        files = files or None

    config = load_file(args.config)
    yaml = create_yaml()
    run(config, files=files, kont=dump_to_yaml, yaml=yaml, config_changed=(files and args.config in files))


if __name__ == "__main__":
    main()
