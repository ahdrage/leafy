#!/usr/bin/env python3
"""Compile the real control core and main.cpp task/transport against SDK doubles.

The extracted functions are verbatim production source, not copies maintained in
the tests. Boundaries must occur exactly once; renamed/moved functions fail the
test build. No ESP-IDF installation or board is needed for these simulations.
"""
import json
import os
from pathlib import Path
import shlex
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src/main.cpp"


def main():
    source = SOURCE.read_text()
    failures = 0
    with tempfile.TemporaryDirectory(prefix="leaf-host-tests-") as directory:
        build = Path(directory)
        for name, start, end in (
            ("can_transport.inc", "static void can_stop(){", "static int read_vpwr(){"),
            ("control_task.inc", "static void control_task(void*){", "static void schedule_reconnect(){"),
        ):
            assert source.count(start) == source.count(end) == 1, name
            first, last = source.index(start), source.index(end)
            assert first < last, name
            line = source[:first].count("\n") + 1
            (build / name).write_text(f"#line {line} {json.dumps(str(SOURCE))}\n" + source[first:last])
        for suite in ("control_test", "battery_task_test", "can_transport_test"):
            binary = build / suite
            command = [os.environ.get("CXX", "clang++"), "-std=c++17", "-Wall", "-Wextra", "-Werror"]
            command += shlex.split(os.environ.get("CXXFLAGS", ""))
            command += ["-I", str(ROOT / "include"), "-I", str(build),
                        str(ROOT / "tests" / f"{suite}.cpp"), "-o", str(binary)]
            subprocess.run(command, check=True)
            print(f"\n{suite}", flush=True)
            failures += subprocess.run([str(binary)], check=False).returncode != 0
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
