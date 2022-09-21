import io
import logging
import urllib
from functools import wraps
from typing import Any, Dict, NamedTuple

import fsspec
import wrapt
import yaml
import yaml.constructor

logger = logging.getLogger(__name__)


def dump_yaml_file(file: io.IOBase, data):
    yaml.dump(data, file, Dumper=YAMLDumper)


class AutoCommitableFileWrapper(wrapt.ObjectProxy):
    def __exit__(self, *args, **kwargs):
        return super().__exit__(*args, **kwargs)

    def close(self):
        f = self.__wrapped__
        if isinstance(f, io.TextIOWrapper):
            f = f.buffer

        self.__wrapped__.close()
        if not f.autocommit:
            logger.debug("commit file %s", f)
            f.commit()

    def __del__(self):
        logger.info("close garbage-collected %s", self)
        self.close()


class FancyDict(dict):
    def __getattr__(self, key):
        if key.startswith("__"):
            return dict.__getattr__(self, key)
        return self[key]

    def __setattr__(self, key, value):
        self[key] = value

    def __delattr__(self, key):
        del self[key]

    def __repr__(self):
        y = yaml.dump({"yaml": self}, Dumper=YAMLDumper)
        assert y.startswith("yaml:")
        return f"<yaml{y[5:]}>"


class BadPythonYAML(NamedTuple):
    tag: str
    value: Any


class YAMLDumper(yaml.Dumper):
    def __init__(self, *args, **kwargs):
        kwargs["indent"] = 4
        kwargs["sort_keys"] = False
        return yaml.Dumper.__init__(self, *args, **kwargs)

    def write_line_break(self, data=None):
        super().write_line_break(data)
        if len(self.indents) == 1:
            super().write_line_break()

    def represent_bad_python_ref(self, data):
        return self.represent_scalar(data.tag, data.value)


class YAMLLoader(yaml.FullLoader):
    def construct_yaml_map(self, node):
        data = FancyDict()
        yield data
        value = self.construct_mapping(node)
        data.update(value)

    def _catch_bad_python_yaml(f):
        @wraps(f)
        def method(self, suffix, node):
            try:
                return f(self, suffix, node)
            except yaml.constructor.ConstructorError:
                return BadPythonYAML(node.tag, node.value)

        return method


def path_fs(path: str) -> fsspec.AbstractFileSystem:
    scheme = urllib.parse.urlparse(path).scheme or "file"
    return fsspec.filesystem(scheme, auto_mkdir=True)


def load_yaml_file(file: io.IOBase) -> Any:
    return yaml.load(file, Loader=YAMLLoader)


def merge_dicts_rec(a: Any, b: Any) -> Dict:
    if isinstance(a, Dict) and isinstance(b, Dict):
        return FancyDict(
            {
                **a,
                **b,
                **{k: merge_dicts_rec(a[k], b[k]) for k in a.keys() & b.keys()},
            }
        )
    elif isinstance(b, Dict):
        return FancyDict(b)
    else:
        return b
