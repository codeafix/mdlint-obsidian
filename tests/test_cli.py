"""CLI tests — focused on exit codes, severity filtering, and JSON output shape."""

import json
import pytest
from mdlint_obsidian.cli import main


def run(argv, capsys):
    """Call main() and return (exit_code, stdout, stderr)."""
    with pytest.raises(SystemExit) as exc:
        main(argv)
    captured = capsys.readouterr()
    return exc.value.code, captured.out, captured.err


class TestExitCodes:
    def test_clean_file_exits_0(self, tmp_path, capsys):
        f = tmp_path / "clean.md"
        f.write_text("# Hello\n\nAll good here.")
        code, _, _ = run([str(f)], capsys)
        assert code == 0

    def test_file_with_errors_exits_1(self, tmp_path, capsys):
        f = tmp_path / "bad.md"
        f.write_text("[[unclosed")
        code, _, _ = run([str(f)], capsys)
        assert code == 1

    def test_warnings_only_exits_0(self, tmp_path, capsys):
        # unclosed-inline-math is a WARNING — should not cause exit 1
        f = tmp_path / "warn.md"
        f.write_text("The value $x is here.")
        code, _, _ = run([str(f)], capsys)
        assert code == 0

    def test_nonexistent_path_exits_2(self, tmp_path, capsys):
        code, _, _ = run([str(tmp_path / "no_such.md")], capsys)
        assert code == 2


class TestSeverityFilter:
    def test_severity_error_suppresses_warnings(self, tmp_path, capsys):
        f = tmp_path / "warn.md"
        f.write_text("The value $x is here.")
        code, out, _ = run([str(f), "--severity", "error"], capsys)
        assert code == 0
        assert out == ""  # warning suppressed, nothing printed

    def test_severity_error_still_shows_errors(self, tmp_path, capsys):
        f = tmp_path / "bad.md"
        f.write_text("[[unclosed")
        code, out, _ = run([str(f), "--severity", "error"], capsys)
        assert code == 1
        assert "unclosed-wikilink" in out


class TestJsonOutput:
    def test_json_format_is_valid_json(self, tmp_path, capsys):
        f = tmp_path / "bad.md"
        f.write_text("[[unclosed")
        _, out, _ = run([str(f), "--format", "json"], capsys)
        parsed = json.loads(out)
        assert isinstance(parsed, list)

    def test_json_entry_has_required_keys(self, tmp_path, capsys):
        f = tmp_path / "bad.md"
        f.write_text("[[unclosed")
        _, out, _ = run([str(f), "--format", "json"], capsys)
        entry = json.loads(out)[0]
        assert {"file", "line", "rule", "severity", "message"} <= entry.keys()

    def test_json_clean_file_returns_empty_list(self, tmp_path, capsys):
        f = tmp_path / "clean.md"
        f.write_text("# Hello")
        _, out, _ = run([str(f), "--format", "json"], capsys)
        assert json.loads(out) == []
