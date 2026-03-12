"""Tests for shared tools (file, git, code analysis)."""

import os
import tempfile
import pytest

from tools.file_tools import read_file, list_directory, read_multiple_files
from tools.code_analysis_tools import find_imports, count_lines


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
