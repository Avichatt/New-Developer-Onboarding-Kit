"""Developer onboarding script with environment checks and reporting."""

import argparse
import shutil
import subprocess
import sys
import time

import requests


def parse_arguments():
    """Parse command-line arguments for verbose and fix modes."""
    parser = argparse.ArgumentParser(description="Check developer environment setup.")
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print extra details for each check.",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Auto-install any missing packages via pip.",
    )
    return parser.parse_args()


def check_python_version(verbose=False):
    """Check that Python version is >= 3.10.

    Returns a tuple of (label, status, elapsed_seconds).
    """
    start = time.time()
    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"
    passed = version.major >= 3 and version.minor >= 10
    status = "PASS" if passed else "FAIL"
    label = f"Python version: {version_str} (>= 3.10 required)"
    elapsed = time.time() - start
    if verbose:
        print(f"    Detail: sys.version_info = {version}")
    return label, status, elapsed


def check_virtual_environment(verbose=False):
    """Check that a virtual environment is currently active.

    Returns a tuple of (label, status, elapsed_seconds).
    """
    start = time.time()
    in_venv = sys.prefix != sys.base_prefix
    venv_name = sys.prefix.split("\\")[-1].split("/")[-1] if in_venv else "None"
    status = "PASS" if in_venv else "FAIL"
    active_label = f"Active ({venv_name})" if in_venv else "Not active"
    label = f"Virtual environment: {active_label}"
    elapsed = time.time() - start
    if verbose:
        print(f"    Detail: sys.prefix = {sys.prefix}")
        print(f"    Detail: sys.base_prefix = {sys.base_prefix}")
    return label, status, elapsed


def check_package(package_name, verbose=False, fix=False):
    """Check if a Python package is installed and return its version.

    Args:
        package_name: Name of the package to check.
        verbose: Whether to print extra detail.
        fix: Whether to attempt auto-install if missing.

    Returns a tuple of (label, status, elapsed_seconds).
    """
    start = time.time()
    try:
        # Use importlib.metadata for reliable version lookup
        from importlib.metadata import version as pkg_version

        ver = pkg_version(package_name)
        status = "PASS"
        label = f"{package_name} installed: version {ver}"
        if verbose:
            import importlib

            mod = importlib.import_module(package_name)
            location = getattr(mod, "__file__", "N/A")
            print(f"    Detail: {package_name} path = {location}")
    except Exception:
        if fix:
            print(f"    [FIX] Installing missing package: {package_name}...")
            subprocess.run(
                [sys.executable, "-m", "pip", "install", package_name],
                check=False,
                capture_output=True,
            )
            # Retry after install
            try:
                from importlib.metadata import version as pkg_version

                ver = pkg_version(package_name)
                status = "PASS"
                label = f"{package_name} installed: version {ver} (auto-installed)"
            except Exception:
                status = "FAIL"
                label = f"{package_name}: NOT installed (install failed)"
        else:
            status = "FAIL"
            label = f"{package_name}: NOT installed"
    elapsed = time.time() - start
    return label, status, elapsed


def check_internet_connectivity(verbose=False):
    """Check internet connectivity by making a request to https://www.google.com.

    Returns a tuple of (label, status, elapsed_seconds).
    """
    start = time.time()
    test_url = "https://www.google.com"
    try:
        response = requests.get(test_url, timeout=5)
        status = "PASS" if response.status_code == 200 else "WARN"
        label = f"Internet connectivity: OK (HTTP {response.status_code})"
        if verbose:
            print(f"    Detail: GET {test_url} -> {response.status_code}")
    except requests.exceptions.ConnectionError:
        status = "FAIL"
        label = "Internet connectivity: FAILED (No connection)"
    except requests.exceptions.Timeout:
        status = "FAIL"
        label = "Internet connectivity: FAILED (Timeout)"
    elapsed = time.time() - start
    return label, status, elapsed


def check_disk_space(verbose=False):
    """Check that free disk space is at least 1 GB.

    Returns a tuple of (label, status, elapsed_seconds).
    """
    start = time.time()
    one_gb = 1_073_741_824
    usage = shutil.disk_usage("/")
    free_gb = usage.free / one_gb
    if usage.free < one_gb:
        status = "WARN"
        label = f"Disk space: LOW — {free_gb:.2f} GB free (< 1 GB recommended)"
    else:
        status = "PASS"
        label = f"Disk space: {free_gb:.2f} GB free"
    elapsed = time.time() - start
    if verbose:
        total_gb = usage.total / one_gb
        used_gb = usage.used / one_gb
        print(
            f"    Detail: total={total_gb:.2f}GB, used={used_gb:.2f}GB, free={free_gb:.2f}GB"
        )
    return label, status, elapsed


def save_report(results, total_elapsed):
    """Save the check results to setup_report.txt.

    Args:
        results: List of (label, status, elapsed) tuples.
        total_elapsed: Total time taken for all checks in seconds.
    """
    report_path = "setup_report.txt"
    passed = sum(1 for _, s, _ in results if s == "PASS")
    total = len(results)
    with open(report_path, "w", encoding="utf-8") as report_file:
        report_file.write("=== Developer Onboarding Check Report ===\n")
        report_file.write(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        for label, status, elapsed in results:
            report_file.write(f"[{status}] {label} [{elapsed:.3f}s]\n")
        report_file.write("\n---\n")
        report_file.write(f"Result: {passed}/{total} checks passed\n")
        report_file.write(f"Total time: {total_elapsed:.3f}s\n")
    return report_path


def main():
    """Run all developer environment checks and print a summary report."""
    args = parse_arguments()
    verbose = args.verbose
    fix = args.fix

    print("=== Developer Onboarding Check ===\n")

    results = []

    # Run all checks
    checks = [
        check_python_version(verbose),
        check_virtual_environment(verbose),
        check_package("pylint", verbose, fix),
        check_package("black", verbose, fix),
        check_package("numpy", verbose, fix),
        check_internet_connectivity(verbose),
        check_disk_space(verbose),
    ]

    for label, status, elapsed in checks:
        icon = (
            "[PASS]"
            if status == "PASS"
            else ("[WARN]" if status == "WARN" else "[FAIL]")
        )
        print(f"{icon} {label} [{elapsed:.3f}s]")
        results.append((label, status, elapsed))

    total_elapsed = sum(e for _, _, e in results)
    passed = sum(1 for _, s, _ in results if s == "PASS")
    total = len(results)

    print("\n---")
    print(f"Result: {passed}/{total} checks passed ✓")
    print(f"Total time: {total_elapsed:.3f}s")

    report_path = save_report(results, total_elapsed)
    print(f"Report saved to: {report_path}")


if __name__ == "__main__":
    main()
