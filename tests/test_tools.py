"""Tests for shared tools (file, git, code analysis, security)."""

import os
import tempfile
import pytest

from tools.file_tools import read_file, list_directory, read_multiple_files
from tools.code_analysis_tools import find_imports, count_lines
from tools.security_tools import (
    scan_for_secrets, detect_injection_sinks, analyze_attack_surface,
    detect_unsafe_deserialization, check_crypto_weaknesses, detect_path_traversal,
)


class TestFileTools:
    """Tests for file system tools."""

    def test_read_file_success(self, tmp_path):
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, World!")
        result = read_file.invoke({"file_path": str(test_file)})
        assert "Hello, World!" in result

    def test_read_file_not_found(self):
        result = read_file.invoke({"file_path": "/nonexistent/file.txt"})
        assert "Error" in result

    def test_list_directory(self, tmp_path):
        (tmp_path / "subdir").mkdir()
        (tmp_path / "file.py").write_text("pass")
        result = list_directory.invoke({"directory_path": str(tmp_path)})
        assert "subdir" in result
        assert "file.py" in result

    def test_list_directory_not_found(self):
        result = list_directory.invoke({"directory_path": "/nonexistent/dir"})
        assert "Error" in result

    def test_read_multiple_files(self, tmp_path):
        f1 = tmp_path / "a.txt"
        f2 = tmp_path / "b.txt"
        f1.write_text("File A")
        f2.write_text("File B")
        result = read_multiple_files.invoke({"file_paths": [str(f1), str(f2)]})
        assert "File A" in result
        assert "File B" in result


class TestCodeAnalysisTools:
    """Tests for code analysis tools."""

    def test_find_imports_python(self, tmp_path):
        py_file = tmp_path / "test.py"
        py_file.write_text("import os\nfrom sys import argv\n\nx = 1\n")
        result = find_imports.invoke({"file_path": str(py_file)})
        assert "import os" in result
        assert "from sys import argv" in result
        assert "2 import" in result

    def test_find_imports_no_imports(self, tmp_path):
        py_file = tmp_path / "test.py"
        py_file.write_text("x = 1\ny = 2\n")
        result = find_imports.invoke({"file_path": str(py_file)})
        assert "No imports" in result

    def test_count_lines(self, tmp_path):
        py_file = tmp_path / "test.py"
        py_file.write_text("# comment\nimport os\n\nx = 1\n")
        result = count_lines.invoke({"file_path": str(py_file)})
        assert "Total lines:" in result
        assert "Code lines:" in result
        assert "Comment lines:" in result
        assert "Blank lines:" in result

    def test_count_lines_not_found(self):
        result = count_lines.invoke({"file_path": "/nonexistent.py"})
        assert "Error" in result


class TestSecurityTools:
    """Tests for exploit-oriented security scanning tools."""

    def test_scan_for_secrets_finds_hardcoded_password(self, tmp_path):
        vuln_file = tmp_path / "config.py"
        vuln_file.write_text('DB_PASSWORD = "super_secret_password_123"\n')
        result = scan_for_secrets.invoke({"directory": str(tmp_path)})
        assert "Hardcoded password" in result

    def test_scan_for_secrets_clean_directory(self, tmp_path):
        clean_file = tmp_path / "app.py"
        clean_file.write_text("import os\nx = os.getenv('PASSWORD')\n")
        result = scan_for_secrets.invoke({"directory": str(tmp_path)})
        assert "No issues found" in result

    def test_detect_injection_sinks_sql(self, tmp_path):
        vuln_file = tmp_path / "db.py"
        vuln_file.write_text('cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")\n')
        result = detect_injection_sinks.invoke({"directory": str(tmp_path)})
        assert "SQL Injection" in result

    def test_detect_injection_sinks_command(self, tmp_path):
        vuln_file = tmp_path / "cmd.py"
        vuln_file.write_text('os.system("rm " + user_input)\n')
        result = detect_injection_sinks.invoke({"directory": str(tmp_path)})
        assert "Command Injection" in result

    def test_detect_injection_sinks_eval(self, tmp_path):
        vuln_file = tmp_path / "danger.py"
        vuln_file.write_text('result = eval(user_expression)\n')
        result = detect_injection_sinks.invoke({"directory": str(tmp_path)})
        assert "Code Injection" in result

    def test_detect_injection_sinks_clean(self, tmp_path):
        clean_file = tmp_path / "safe.py"
        clean_file.write_text("x = 1 + 2\nprint(x)\n")
        result = detect_injection_sinks.invoke({"directory": str(tmp_path)})
        assert "No issues found" in result

    def test_analyze_attack_surface(self, tmp_path):
        flask_file = tmp_path / "routes.py"
        flask_file.write_text('@app.route("/api/users", methods=["GET"])\ndef get_users():\n    pass\n')
        result = analyze_attack_surface.invoke({"directory": str(tmp_path)})
        assert "HTTP Route Handler" in result

    def test_detect_unsafe_deserialization_pickle(self, tmp_path):
        vuln_file = tmp_path / "loader.py"
        vuln_file.write_text('import pickle\ndata = pickle.load(open("data.pkl", "rb"))\n')
        result = detect_unsafe_deserialization.invoke({"directory": str(tmp_path)})
        assert "Pickle deserialization" in result

    def test_detect_unsafe_deserialization_yaml(self, tmp_path):
        vuln_file = tmp_path / "config_loader.py"
        vuln_file.write_text('import yaml\ndata = yaml.load(open("config.yml"))\n')
        result = detect_unsafe_deserialization.invoke({"directory": str(tmp_path)})
        assert "Unsafe YAML" in result

    def test_check_crypto_weaknesses_md5(self, tmp_path):
        vuln_file = tmp_path / "hash.py"
        vuln_file.write_text('import hashlib\nh = hashlib.md5(password.encode())\n')
        result = check_crypto_weaknesses.invoke({"directory": str(tmp_path)})
        assert "MD5" in result

    def test_check_crypto_weaknesses_ssl_disabled(self, tmp_path):
        vuln_file = tmp_path / "api.py"
        vuln_file.write_text('requests.get(url, verify=False)\n')
        result = check_crypto_weaknesses.invoke({"directory": str(tmp_path)})
        assert "SSL verification disabled" in result

    def test_detect_path_traversal(self, tmp_path):
        vuln_file = tmp_path / "download.py"
        vuln_file.write_text('f = open(os.path.join(base, "../../../etc/passwd"))\n')
        result = detect_path_traversal.invoke({"directory": str(tmp_path)})
        assert "traversal" in result.lower() or "Path" in result
