"""A small metric layer.

Reads metrics.yml, builds the staging model, runs the data tests, and compiles
metric requests into SQL. Every number in the analysis that is a *definition*
(a rate, a lift, a dollar value) comes from here. The analysis code adds only
uncertainty (confidence intervals, bootstrap) on top of these definitions.

Usage:
    python -m metrics.layer build            # load data, build model, run tests
    python -m metrics.layer sql net_value_per_send --dims split
    python -m metrics.layer query incremental_response_rate net_value_per_send --dims split
"""

from __future__ import annotations

import argparse
import re
import sqlite3
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
METRICS_DIR = ROOT / "metrics"
DATA_DIR = ROOT / "data"
RAW_COLUMNS = ["ID", "Promotion", "purchase", "V1", "V2", "V3", "V4", "V5", "V6", "V7"]


class MetricLayer:
    def __init__(self, spec_path: Path = METRICS_DIR / "metrics.yml", conn: sqlite3.Connection | None = None):
        self.spec = yaml.safe_load(spec_path.read_text())
        self.conn = conn or sqlite3.connect(":memory:")
        self.econ = self.spec["economics"]
        self.measures = self.spec["measures"]
        self.metrics = self.spec["metrics"]
        self.dimensions = self.spec["dimensions"]
        self.model = self.spec["model"]["name"]

    # ---------- build ----------
    def load_raw(self) -> None:
        for table, fname in [("raw_training", "training.csv"), ("raw_test", "Test.csv")]:
            path = DATA_DIR / fname
            if not path.exists():
                raise FileNotFoundError(f"{path} missing. Run data/download.sh first.")
            df = pd.read_csv(path, usecols=RAW_COLUMNS)
            df.to_sql(table, self.conn, index=False, if_exists="replace")

    def build_model(self) -> None:
        sql = (METRICS_DIR / self.spec["model"]["sql"]).read_text()
        self.conn.execute(f"drop table if exists {self.model}")
        self.conn.execute(f"create table {self.model} as {sql}")

    def run_tests(self) -> list[dict]:
        results = []
        for t in self.spec.get("tests", []):
            got = self.conn.execute(t["sql"]).fetchone()[0]
            results.append({"test": t["name"], "expected": t["expect"], "got": got, "passed": got == t["expect"]})
        failed = [r for r in results if not r["passed"]]
        if failed:
            raise AssertionError(f"Data tests failed: {failed}")
        return results

    def build(self) -> list[dict]:
        self.load_raw()
        self.build_model()
        return self.run_tests()

    # ---------- compile ----------
    def _fill_econ(self, expr: str) -> str:
        for k, v in self.econ.items():
            expr = expr.replace("{" + k + "}", repr(float(v)))
        return expr

    def compile(self, name: str) -> str:
        """Return a SQL aggregate expression for a measure or metric."""
        if name in self.measures:
            return self.measures[name]["agg"]
        if name not in self.metrics:
            raise KeyError(f"Unknown metric or measure: {name}")
        m = self.metrics[name]
        if m["type"] == "ratio":
            num, den = self.compile(m["numerator"]), self.compile(m["denominator"])
            return f"(cast({num} as real) / nullif({den}, 0))"
        if m["type"] == "derived":
            expr = self._fill_econ(m["expr"])
            refs = sorted(set(self.metrics) | set(self.measures), key=len, reverse=True)
            for ref in refs:
                if ref == name:
                    continue
                expr = re.sub(rf"\b{re.escape(ref)}\b", lambda _m, r=ref: f"({self.compile(r)})", expr)
            return f"({expr})"
        raise ValueError(f"Unsupported metric type: {m['type']}")

    def sql(self, names: list[str], dims: list[str] | None = None, where: str | None = None) -> str:
        dims = dims or []
        for d in dims:
            if d not in self.dimensions:
                raise KeyError(f"Unknown dimension: {d}")
        select = [f"{self.dimensions[d]['expr']} as {d}" for d in dims]
        select += [f"{self.compile(n)} as {n}" for n in names]
        q = f"select\n    " + ",\n    ".join(select) + f"\nfrom {self.model}"
        if where:
            q += f"\nwhere {where}"
        if dims:
            q += "\ngroup by " + ", ".join(dims) + "\norder by " + ", ".join(dims)
        return q

    def query(self, names: list[str], dims: list[str] | None = None, where: str | None = None) -> pd.DataFrame:
        return pd.read_sql_query(self.sql(names, dims, where), self.conn)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("command", choices=["build", "sql", "query"])
    p.add_argument("names", nargs="*")
    p.add_argument("--dims", default="")
    p.add_argument("--where", default=None)
    a = p.parse_args()
    dims = [d for d in a.dims.split(",") if d]
    layer = MetricLayer()
    if a.command == "sql":
        print(layer.sql(a.names, dims, a.where))
        return
    for r in layer.build():
        print(f"[{'PASS' if r['passed'] else 'FAIL'}] {r['test']}")
    if a.command == "query":
        print(layer.query(a.names, dims, a.where).to_string(index=False))


if __name__ == "__main__":
    main()
