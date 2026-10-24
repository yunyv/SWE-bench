"""Suite identities in ordinary karma-mocha-reporter output."""

import pytest

from swebench.harness.constants import END_TEST_OUTPUT, START_TEST_OUTPUT
from swebench.harness.grading import get_eval_report
from swebench.harness.log_parsers import PARSER_REGISTRY
from swebench.types import TestSpec as SweTestSpec


@pytest.mark.parametrize(
    ("body", "expected"),
    [
        (
            "  Alpha\n    ✔ renders\n  Beta\n    ✖ renders\n",
            {"Alpha > renders": "PASSED", "Beta > renders": "FAILED"},
        ),
        (
            "  Root\n    Alpha\n      ✔ renders\n    Beta\n      ✖ renders\n",
            {"Root > Alpha > renders": "PASSED", "Root > Beta > renders": "FAILED"},
        ),
        (
            "  Root\n    Child\n      Deep\n        ✔ nested\n  Other\n    ✖ renders\n",
            {"Root > Child > Deep > nested": "PASSED", "Other > renders": "FAILED"},
        ),
        (
            "  Root\n    Child\n      ✔ nested\n    ✖ parent test\n",
            {"Root > Child > nested": "PASSED", "Root > parent test": "FAILED"},
        ),
        (
            "  Root\n    ✔ first\n    ✖ second\n",
            {"Root > first": "PASSED", "Root > second": "FAILED"},
        ),
        ("  ✔ root test\n", {"root test": "PASSED"}),
        ("  Root\n    Child\n      ✔ nested\n", {"Root > Child > nested": "PASSED"}),
    ],
    ids=[
        "root-siblings",
        "nested-siblings",
        "multi-level-dedent",
        "parent-test",
        "same-suite",
        "root-test",
        "nested-control",
    ],
)
def test_karma_suite_paths(body, expected):
    log = (
        "Starting browser ChromeHeadless\n"
        + body
        + "SUMMARY:\n  ignored\n    ✖ detail\n"
    )
    assert PARSER_REGISTRY["parse_log_karma"](log, None) == expected


def test_karma_ignores_results_before_browser_start():
    assert PARSER_REGISTRY["parse_log_karma"]("  Root\n    ✔ test\n", None) == {}


@pytest.mark.parametrize("symbol, resolved", [("✔", True), ("✖", False)])
def test_karma_grading_preserves_sibling_test_identity(tmp_path, symbol, resolved):
    spec = SweTestSpec(
        instance_id="synthetic-karma",
        image="unused",
        eval_script_list=[],
        repo="preactjs/preact",
        version="synthetic",
        FAIL_TO_PASS=["Beta > renders"],
        PASS_TO_PASS=["Alpha > renders"],
        log_parser="parse_log_karma",
        eval_type="pass_and_fail",
    )
    output = tmp_path / "test_output.txt"
    output.write_text(
        f"{START_TEST_OUTPUT}\nStarting browser ChromeHeadless\n"
        f"  Alpha\n    ✔ renders\n  Beta\n    {symbol} renders\nSUMMARY:\n"
        f"{END_TEST_OUTPUT}\n"
    )
    prediction = {
        "instance_id": spec.instance_id,
        "model_patch": "synthetic grader input",
    }
    report = get_eval_report(spec, prediction, str(output), True)[spec.instance_id]
    assert report["tests_status"]["PASS_TO_PASS"]["success"] == ["Alpha > renders"]
    assert report["resolved"] is resolved
