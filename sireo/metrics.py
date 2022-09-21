from __future__ import annotations

import datetime
import json
import logging
from collections import defaultdict
from pathlib import Path
from typing import Union

import pandas as pd

import sireo

logger = logging.getLogger(__name__)


class MetricsExporter:
    def __init__(
        self,
        tracker: sireo.core.Tracker,
        metrics_per_file=10000,
        filename="metrics",
        add_uuid=None,
    ):
        self.tracker = tracker
        self.metricss = defaultdict(list)
        self.metrics_per_file = metrics_per_file
        self.metrics_cnt = 0
        self.filename = filename
        self.formats = {}
        self._rslug = f"-{add_uuid}" if add_uuid else ""

    def meter(self, kvs, series, format):
        format = format or "csv"
        assert format in {"jsonl", "csv"}
        assert self.formats.setdefault(series, format) == format

        series = series or ""
        metrics = self.metricss[series]
        if len(metrics) >= self.metrics_per_file:
            self.flush()
        d = dict(kvs)
        d["at"] = datetime.datetime.now().timestamp()
        metrics.append(d)

    def flush_series(self, series):
        format = self.formats[series]
        metrics = self.metricss[series]
        if not metrics:
            return

        if series:
            mfile = (
                f"{self.filename}{self._rslug}-{self.metrics_cnt:04}-{series}.{format}"
            )
        else:
            mfile = f"{self.filename}{self._rslug}-{self.metrics_cnt:04}.{format}"

        logger.debug("write metrics to %s", mfile)
        wf = {
            "csv": self._write_metrics_file_csv,
            "jsonl": self._write_metrics_file_jsonl,
        }[format]
        with self.tracker.attach(mfile, mode="wt") as f:
            wf(f, metrics)

        metrics.clear()
        self.metrics_cnt += 1

    def _write_metrics_file_jsonl(self, f, metrics):
        for m in metrics:
            json.dump(m, f, sort_keys=True)
            f.write("\n")

    def _write_metrics_file_csv(self, f, metrics):
        df = pd.DataFrame(metrics)
        df.set_index("at", inplace=True)
        df.to_csv(f)

    def flush(self):
        for s in self.metricss:
            self.flush_series(s)
