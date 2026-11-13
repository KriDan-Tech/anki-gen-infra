#!/usr/bin/env python3
"""VM-only three-suite regression preset. See run-vnext-regression.md.

API references: Python 3.12 stdlib sources (/usr/lib/python3.12/{argparse,
pathlib,shutil,subprocess,hashlib,json,shlex,xml/etree/ElementTree}.py);
Docker run/image inspect --help on external-docker; os.killpg/umask:
https://docs.python.org/3.12/library/os.html; Angular build 22.2.4
unit-test/schema.json; extractor scripts/test-usage-isolated.sh (Maven 3.9).
No dependency installation, deployment, optional benchmarks, or provider calls.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import signal
import socket
import subprocess
import sys
import time
import xml.etree.ElementTree as ET


EXCLUDED = {
    ".git", ".venv", "venv", "node_modules", "target", "private",
    "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
    ".cache", "cache", "caches", ".angular", ".npm", ".m2", ".serena",
    "dist", "build", "coverage", ".coverage", ".npmrc", ".pypirc",
    "settings.xml", ".ssh", ".aws", ".azure", ".kube", ".docker",
    "test-usage-vm-run.sh",
}
ANSI = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")


def excluded(name):
    return (
        name in EXCLUDED or name.startswith(".env")
        or name.lower().endswith((".pem", ".key", ".p12", ".pfx"))
        or name.startswith(("id_rsa", "id_ed25519"))
    )


def ignore_source(directory, names):
    # Never follow source symlinks into private or out-of-tree inputs.
    return [n for n in names if excluded(n) or (Path(directory) / n).is_symlink()]


def digest(path):
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def execute(command, log, env, timeout):
    """Keep all child output off the terminal and bound the complete process group."""
    with log.open("a", encoding="utf-8") as output:
        output.write("$ " + shlex.join(command) + "\n")
        output.flush()
        process = subprocess.Popen(
            command, stdout=output, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
            env=env, start_new_session=True,
        )
        try:
            return process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            output.write("\nSuite command timed out.\n")
            output.flush()
            # Killing the group also stops the wrapper's docker client/children.
            # Suite cleanup below removes any server-side containers.
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()
            return 124


def cleanup_resources(names, network, log, env):
    """Removal exit codes are not proof of cleanup: verify daemon-side absence."""
    evidence = {"attempts": [], "verified_absent": True}
    commands = ([["docker", "rm", "-f", *names]] if names else [])
    if network:
        commands.append(["docker", "network", "rm", network])
    for command in commands:
        attempt = {"command": command}
        try:
            attempt["exit_code"] = execute(command, log, env, 30)
        except Exception as error:
            attempt["error"] = str(error)
        evidence["attempts"].append(attempt)
    # VERIFIED: Docker 29.9.3 container/network ls --help on external-docker;
    # --all and --format expose exact task-owned names for absence checks.
    for kind, expected, command in (
        ("containers", names,
         ["docker", "container", "ls", "--all", "--format", "{{.Names}}"]),
        ("networks", [network] if network else [],
         ["docker", "network", "ls", "--format", "{{.Name}}"]),
    ):
        if not expected:
            continue
        verification = {"expected_absent": expected}
        try:
            checked = subprocess.run(
                command, capture_output=True, text=True, env=env, timeout=30, check=False,
            )
            verification["exit_code"] = checked.returncode
            with log.open("a", encoding="utf-8") as output:
                output.write("$ " + shlex.join(command) + "\n")
                output.write(checked.stdout + checked.stderr)
            if checked.returncode:
                raise ValueError("Cannot verify absence of " + kind)
            remaining = sorted(set(expected) & set(checked.stdout.splitlines()))
            verification["remaining"] = remaining
            if remaining:
                evidence["verified_absent"] = False
        except Exception as error:
            verification["error"] = str(error)
            evidence["verified_absent"] = False
        evidence[kind] = verification
    return evidence


def snapshot(source, destination, env):
    shutil.copytree(source, destination, ignore=ignore_source)
    files = {
        str(p.relative_to(destination)): digest(p)
        for p in sorted(destination.rglob("*")) if p.is_file()
    }
    sha = None
    try:
        resolved = subprocess.run(
            ["git", "-C", str(source), "rev-parse", "HEAD"],
            capture_output=True, text=True, env=env, check=False, timeout=30,
        )
        if resolved.returncode == 0:
            sha = resolved.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        pass  # Exported snapshots may have no Git executable/metadata.
    # A Git SHA alone is insufficient for dirty trees: hash every included file.
    return {
        "input": str(source), "git_sha": sha,
        "files_sha256": files, "file_count": len(files),
    }


def xml_counts(paths):
    totals = dict(tests=0, passed=0, failures=0, errors=0, skipped=0)
    if not paths:
        raise ValueError("No fresh XML reports were produced")
    for path in paths:
        root = ET.parse(path).getroot()
        suites = [root] if root.tag == "testsuite" else list(root.iter("testsuite"))
        # JUnit aggregate parents can otherwise double-count child suites.
        for suite in suites:
            if suite.find("testsuite") is not None:
                continue
            for field in ("tests", "failures", "errors", "skipped"):
                totals[field] += int(suite.get(field, "0"))
    totals["passed"] = (
        totals["tests"] - totals["failures"] - totals["errors"] - totals["skipped"]
    )
    if totals["tests"] == 0:
        raise ValueError("Reports contain zero tests")
    return totals


def frontend_counts(log):
    text = ANSI.sub("", log.read_text(encoding="utf-8", errors="replace"))
    lines = re.findall(r"^\s*Tests\s+(.+)$", text, re.MULTILINE)
    if not lines:
        raise ValueError("No completed frontend Tests summary (see log)")
    counts = dict(tests=0, passed=0, failures=0, errors=0, skipped=0)
    for number, label in re.findall(r"(\d+)\s+(passed|failed|skipped|todo)", lines[-1]):
        field = {"passed": "passed", "failed": "failures", "skipped": "skipped",
                 "todo": "skipped"}[label]
        counts[field] += int(number)
        counts["tests"] += int(number)
    if not counts["tests"]:
        raise ValueError("Frontend summary contains zero tests")
    return counts


def copy_node_modules(source, destination):
    if not source.is_dir():
        raise ValueError("Supply VM node_modules with --node-modules (no npm install)")
    def ignore(directory, names):
        rejected = []
        for name in names:
            path = Path(directory) / name
            # Dependency dist/build/nested node_modules are essential runtime files.
            secret = name.startswith(".env") or name in {
                ".git", ".npmrc", ".pypirc", "settings.xml",
            } or name.lower().endswith((".pem", ".key", ".p12", ".pfx"))
            if secret or (
                path.is_symlink() and not path.resolve().is_relative_to(source)
            ):
                rejected.append(name)
        return rejected
    # Preserve npm's relative .bin links, but not links outside the supplied tree.
    shutil.copytree(source, destination, symlinks=True, ignore=ignore)


def adapt_java(snapshot_dir, temporary, cache, prefix):
    original = snapshot_dir / "scripts/test-usage-isolated.sh"
    text = original.read_text(encoding="utf-8")
    replacements = {
        "/mnt/hdd/tmp/extractor-usage-test.XXXXXX":
            shlex.quote(str(temporary / "extractor-usage-test.XXXXXX")),
        "-v /mnt/hdd/cache/yookassa-m2:/root/.m2":
            "-v " + shlex.quote(str(cache) + ":/root/.m2"),
        "run=usage-isolated-$$": "run=" + shlex.quote(prefix),
        "docker run --rm --network":
            "docker run --rm --name " + shlex.quote(prefix + "-maven") + " --network",
    }
    for old, new in replacements.items():
        if text.count(old) != 1:
            raise ValueError("Java wrapper changed; expected exactly one " + old)
        text = text.replace(old, new)
    adapted = snapshot_dir / "scripts/test-usage-vm-run.sh"
    adapted.write_text(text, encoding="utf-8")
    return adapted


def arguments():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("source", "extractor", "frontend", "run-dir"):
        parser.add_argument("--" + name, required=True, type=Path)
    parser.add_argument("--python-image", default="task043-v2-test:latest")
    parser.add_argument("--frontend-image", default="node:24-bookworm-slim")
    parser.add_argument("--node-modules", type=Path,
                        help="VM dependency directory; default: FRONTEND/node_modules")
    parser.add_argument("--maven-cache", type=Path,
                        default=Path.home() / ".cache/anki-regression-m2")
    parser.add_argument("--suite-timeout", type=int, default=1800, metavar="SECONDS")
    parser.add_argument("--vm-machine-id",
                        help="Explicit previously verified VM /etc/machine-id if hostname changed")
    args = parser.parse_args()
    hostname = socket.gethostname()
    verified_identity = False
    if args.vm_machine_id:
        machine_id = Path("/etc/machine-id").read_text(encoding="ascii").strip()
        verified_identity = bool(re.fullmatch(r"[0-9a-f]{32}", args.vm_machine_id)) and (
            machine_id == args.vm_machine_id
        )
        if not verified_identity:
            parser.error("VM machine identity does not match")
    if hostname != "external-docker" and not verified_identity:
        parser.error("VM only: execute via ssh docker-vm (expected external-docker)")
    if args.suite_timeout <= 0:
        parser.error("--suite-timeout must be positive")
    for name in ("source", "extractor", "frontend", "run_dir", "maven_cache"):
        setattr(args, name, getattr(args, name).expanduser().resolve())
    args.node_modules = (
        args.node_modules.expanduser().resolve() if args.node_modules
        else args.frontend / "node_modules"
    )
    for source in (args.source, args.extractor, args.frontend):
        if not source.is_dir():
            parser.error("Input must be an existing directory: " + str(source))
        if args.run_dir.is_relative_to(source) or source.is_relative_to(args.run_dir):
            parser.error("--run-dir must be separate from all input trees")
    if args.run_dir.exists():
        parser.error("--run-dir already exists; choose a fresh path")
    for cache in (args.maven_cache, args.node_modules):
        if cache.is_relative_to(args.run_dir) or args.run_dir.is_relative_to(cache):
            parser.error("Caches/dependencies must be separate from --run-dir")
    for path in (args.run_dir, args.maven_cache):
        if ":" in str(path) or "\n" in str(path):
            parser.error("Docker volume paths cannot contain colons or newlines")
    return args


def main():
    args = arguments()
    os.umask(0o077)
    args.run_dir.mkdir(mode=0o700, parents=True)  # Atomic freshness check; never exist_ok.
    logs = args.run_dir / "logs"
    reports = args.run_dir / "reports"
    temporary = args.run_dir / "tmp"
    home = args.run_dir / "home"
    for directory in (logs, reports, temporary, home, args.run_dir / "snapshots"):
        directory.mkdir()
    # No inherited service credentials, Docker context, env files, npmrc or Maven opts.
    env = {
        "PATH": "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
        "HOME": str(home), "TMPDIR": str(temporary), "LANG": "C.UTF-8",
    }
    prefix = "vnext-" + hashlib.sha256(str(args.run_dir).encode()).hexdigest()[:16]
    summary = {
        "schema_version": 1, "hostname": socket.gethostname(), "run_dir": str(args.run_dir),
        "started_at_unix": time.time(), "suite_timeout_seconds": args.suite_timeout,
        "suites": {}, "provenance": {},
    }

    def image_check(image, result, log):
        # Preinstalled images only; inspecting first also prevents Java's implicit pulls.
        checked = subprocess.run(
            ["docker", "image", "inspect", "--format", "{{.Id}}", image],
            capture_output=True, text=True, env=env, timeout=30, check=False,
        )
        with log.open("a", encoding="utf-8") as stream:
            stream.write(checked.stderr)
        if checked.returncode:
            raise ValueError("Required VM image is unavailable: " + image)
        result.setdefault("images", {})[image] = checked.stdout.strip()

    for suite, source in (
        ("python", args.source), ("frontend", args.frontend), ("java", args.extractor)
    ):
        started = time.monotonic()
        log = logs / (suite + ".log")
        log.touch(mode=0o600)
        result = {"status": "FAIL", "exit_code": None, "log": str(log), "counts": None}
        names = []
        java_network = None
        try:
            staged = args.run_dir / "snapshots" / suite
            summary["provenance"][suite] = snapshot(source, staged, env)
            suite_reports = reports / suite
            suite_reports.mkdir()
            if suite in ("python", "frontend"):
                image = args.python_image if suite == "python" else args.frontend_image
                image_check(image, result, log)
                name = prefix + "-" + suite
                names = [name]
                command = [
                    "docker", "run", "--rm", "--pull", "never", "--name", name,
                    "--network", "none",
                ]
                if suite == "python":
                    command += [
                        "--read-only", "--tmpfs", "/tmp:rw",
                        "-e", "PYTHONDONTWRITEBYTECODE=1", "-e", "PYTEST_ADDOPTS=",
                        "-v", str(staged) + ":/app:ro",
                        "-v", str(suite_reports) + ":/reports", "-w", "/app",
                        "--entrypoint", "python", image,
                        "-m", "pytest", "-q", "-p", "no:cacheprovider",
                        "--junitxml=/reports/pytest.xml",
                    ]
                else:
                    # Hash source BEFORE adding dependencies or generating build artifacts.
                    copy_node_modules(args.node_modules, staged / "node_modules")
                    result["node_modules"] = str(args.node_modules)
                    command += [
                        "-e", "CI=true", "-e", "NG_CLI_ANALYTICS=false",
                        "-v", str(staged) + ":/app", "-w", "/app", image,
                        "npm", "test", "--", "--watch=false",
                    ]
            else:
                for image in ("postgres:17", "rabbitmq:4-management",
                              "maven:3.9-eclipse-temurin-21"):
                    image_check(image, result, log)
                args.maven_cache.mkdir(parents=True, exist_ok=True)
                if (args.maven_cache / "settings.xml").exists():
                    raise ValueError("Use a dedicated Maven cache without settings.xml credentials")
                wrapper = adapt_java(staged, temporary, args.maven_cache, prefix)
                result["staged_wrapper_sha256"] = digest(wrapper)
                result["maven_cache"] = str(args.maven_cache)
                names = [prefix + suffix for suffix in ("-db", "-rabbit", "-maven")]
                java_network = prefix
                command = ["bash", str(wrapper)]
            result["exit_code"] = execute(command, log, env, args.suite_timeout)
            if suite == "python":
                report_paths = [suite_reports / "pytest.xml"]
                result["counts"] = xml_counts(report_paths)
                text = log.read_text(encoding="utf-8", errors="replace")
                subtests = re.findall(r"(\d+) subtests? passed", text)
                if subtests:
                    # Pytest 9 includes passed subtests in JUnit totals separately.
                    number = int(subtests[-1])
                    result["counts"]["subtests_passed"] = number
                    result["counts"]["junit_tests"] = result["counts"]["tests"]
                    result["counts"]["tests"] -= number
                    result["counts"]["passed"] -= number
            elif suite == "frontend":
                result["counts"] = frontend_counts(log)
                report_paths = []
            else:
                # Only this invocation's fresh mktemp build, never an input target/ tree.
                text = log.read_text(encoding="utf-8", errors="replace")
                artifacts = re.findall(r"^Verification artifacts: (.+)$", text, re.MULTILINE)
                if artifacts:
                    build = Path(artifacts[-1]).resolve()
                    if build.parent != temporary or not build.name.startswith("extractor-usage-test."):
                        raise ValueError("Java artifact path is outside this run")
                else:
                    # Wrapper exits before printing artifacts on Maven failure.
                    builds = sorted(temporary.glob("extractor-usage-test.*"))
                    if len(builds) != 1:
                        raise ValueError("Cannot identify this invocation's Java artifacts")
                    build = builds[0]
                result["artifacts"] = str(build)
                report_paths = sorted(build.glob("target/surefire-reports/TEST-*.xml"))
                report_paths += sorted(build.glob("target/failsafe-reports/TEST-*.xml"))
                result["counts"] = xml_counts(report_paths)
            result["reports"] = [str(path) for path in report_paths]
            counts = result["counts"]
            if result["exit_code"] == 0 and not (counts["failures"] or counts["errors"]):
                result["status"] = "PASS"
        except Exception as error:
            result["error"] = str(error)
            with log.open("a", encoding="utf-8") as stream:
                stream.write("\nPreset error: " + str(error) + "\n")
        finally:
            result["cleanup"] = cleanup_resources(names, java_network, log, env)
            if not result["cleanup"]["verified_absent"]:
                result["status"] = "FAIL"
                result["cleanup_error"] = "Resources remain or absence could not be verified"
            result["duration_seconds"] = round(time.monotonic() - started, 2)
            summary["suites"][suite] = result
            summary["status"] = "RUNNING"
            write_json(args.run_dir / "summary.json", summary)
            counts = result["counts"]
            detail = (
                " ".join(str(counts[key]) + " " + label for key, label in (
                    ("passed", "passed"), ("failures", "failed"),
                    ("errors", "errors"), ("skipped", "skipped")
                )) if counts else "counts unavailable"
            )
            if counts and counts.get("subtests_passed"):
                detail += f" +{counts['subtests_passed']} subtests"
            print(f"{suite}: {result['status']} {detail} "
                  f"({result['duration_seconds']}s) log={log}", flush=True)

    summary["finished_at_unix"] = time.time()
    summary["status"] = (
        "PASS" if all(s["status"] == "PASS" for s in summary["suites"].values()) else "FAIL"
    )
    write_json(args.run_dir / "summary.json", summary)
    print(f"{summary['status']} summary={args.run_dir / 'summary.json'}", flush=True)
    return 0 if summary["status"] == "PASS" else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError) as error:
        print("Preset setup failed: " + str(error), file=sys.stderr)
        sys.exit(2)
