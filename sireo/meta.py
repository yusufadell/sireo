import logging
import typing

logger = logging.getLogger(__name__)
from .data import FancyDict, merge_dicts_rec

providers: typing.Dict[str, typing.Callable[[], str]] = {}


class NoMetadataException(Exception):
    pass


def capture_meta(ps=None) -> FancyDict:
    if ps is None:
        ps = providers
    metas = {}
    for key, provider in ps.items():

        logger.info("capture metadata %r", key)
        try:
            m = provider()
        except NoMetadataException:
            continue
        except Exception as e:
            logger.warning("failed to capture %r: %s", key, e)
            continue

        if m is not None:
            sections = key.split(".")
            md = {sections[-1]: m}
            for s in sections[:-1]:
                md = {s: md}
            metas = merge_dicts_rec(metas, md)

    return FancyDict(metas)
