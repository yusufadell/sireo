"""Top-level package for sireo."""

__author__ = """Yusuf Adel"""
__email__ = "yusufadell.dev@gmail.com"
__version__ = "0.1.0"

import atexit
import contextlib
import contextvars
import datetime
import functools
import inspect
import logging
import typing
from os import PathLike
from typing import Callable, Dict, Optional, Union

from . import core, hook, meta
from . import runner as _vtvt_runner

try:
    # extends python's pickle module for serializing and de-serializing
    import dill
except ImportError:
    dill = None

logger = logging.getLogger(__name__)
_T = typing.TypeVar("_T")


_var_tracker = contextvars.ContextVar("sireo._var_tracker")
_global_runner = None

__all__ = [
    "track",
    "init",
    "run",
]


@contextlib.contextmanager
def using_tracker(tracker: core.ATracker, globally: bool = False):
    global _global_tracker

    if globally and _global_tracker is not None or _var_tracker.get(None) is not None:
        raise RuntimeError("A tracker is already configured")

    try:
        logger.debug("enter tracker %s", tracker)
        if globally:
            _global_tracker = tracker
        else:
            t = _var_tracker.set(tracker)
        tracker.activate()
        yield
    finally:
        logger.debug("exit tracker %s", tracker)
        try:
            tracker.flush()
        except Exception:
            logging.exception("Unable to flush tracker")
        if globally:
            _global_tracker = None
        else:
            _var_tracker.reset(t)


def init(
    path: str | PathLike = ".",
    hooks: hook.Hook | list[hook.Hook] | None = None,
    runner: str | type[_vtvt_runner.ARunner] = "inplace",
    meta_providers: dict[str, Callable[[], str]] | None = None,
    **kwargs,
) -> None:

    global _global_runner

    if isinstance(runner, type):
        runner_cls = runner
    else:
        runner_cls = _vtvt_runner.find_runner(runner)

    metap = meta_providers or meta.providers

    logger.debug("Create global runner of type %s", runner_cls)
    _global_runner = runner_cls(
        metap=metap,
        path=path,
        hook=hooks,
        **kwargs,
    )

    atexit.register(lambda: _global_runner.close())


def run(tid: str, fn: Callable[..., _T], /, **params: Dict) -> core.Trial:
    if _global_runner is None:
        raise RuntimeError("Runner is not initialized, call `sireo.init(...) first`")
    return _global_runner.run(tid, fn, **params)


def _default_tid(**kwargs):
    return datetime.datetime.now().strftime("%y-%m-%d/%H:%M:%S")


def track(
    name: Optional[str] = None,
    tid_pattern: Union[str, Callable, None] = None,
    rand_slug: bool = True,
):
    def wrapper(f: _T) -> _T:
        if name is None:
            name_prefix = f"{f.__module__}.{f.__qualname__}/"
        elif name:
            name_prefix = name + "/"
        else:
            name_prefix = ""

        if tid_pattern is None:
            tidp = _default_tid
        elif isinstance(tid_pattern, str):
            tidp = tid_pattern.format
        elif isinstance(tid_pattern, Callable):
            tidp = tid_pattern
        else:
            raise ValueError(
                f"invalid tid pattern {tid_pattern}, expected string or callable"
            )

        if rand_slug:
            import uuid

            suffixc = lambda: "/" + uuid.uuid1().hex
        else:
            suffixc = lambda: ""
        argspec = inspect.getfullargspec(f)
        sig = inspect.signature(f)

        @functools.wraps(f)
        def g(*args, **kwargs):
            params = dict(sig.bind(*args, **kwargs).arguments)
            if argspec.varkw:
                params.update(params.pop(argspec.varkw, {}))

            tid = name_prefix + tidp(**params) + suffixc()
            return run(tid, captured_f, **params).result

        if dill:
            # `dill` is able to serialize mutated global function,
            # but fails to serialize recursive closure (when `g` captures itself)
            captured_f = f
        else:
            # `pickle` verify that global function remains the same
            # so `g` needs to capture link to itself
            captured_f = g

        g._sireo__wrapped_fn = f
        return g

    return wrapper
