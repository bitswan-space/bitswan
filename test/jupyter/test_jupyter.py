from bspump.main import NotebookCompiler, indent_code
from bspump.notebook_traceback import rewrite_traceback_string
import json
import ast


def test_notebook_parse_valid():
    compiler = NotebookCompiler()
    with open("jupyter/parse_example.ipynb", "r") as ntbf:
        ntb = json.load(ntbf)
    compiler.compile_notebook(ntb, "jupyter/tmp.py")
    with open("jupyter/tmp.py", "r") as outf:
        out = ast.parse(outf.read())
    with open("jupyter/expected.py", "r") as expectf:
        expect = ast.parse(expectf.read())
    assert ast.dump(out) == ast.dump(expect)


def test_notebook_formatting():
    compiler = NotebookCompiler()
    with open("jupyter/parse_example.ipynb", "r") as ntbf:
        ntb = json.load(ntbf)
    compiler.compile_notebook(ntb, "jupyter/tmp.py")
    with open("jupyter/tmp.py", "r") as outf:
        out = outf.read()
    with open("jupyter/expected.py", "r") as expectf:
        expect = expectf.read()
    assert out == expect


def test_indent_code_single_line_double_quotes():
    lines = [
        'x = """hello"""',
        "y = 1",
    ]
    result = indent_code(lines)
    assert result == [
        '    x = """hello"""',
        "    y = 1",
    ]


def test_indent_code_single_line_single_quotes():
    lines = [
        "x = '''hello'''",
        "y = 1",
    ]
    result = indent_code(lines)
    assert result == [
        "    x = '''hello'''",
        "    y = 1",
    ]


def test_indent_code_multiline_still_works():
    lines = [
        'my_string = """a line',
        "non-indented line",
        "    once indented line",
        '"""',
        "y = 1",
    ]
    result = indent_code(lines)
    assert result == [
        '    my_string = """a line',
        "non-indented line",
        "    once indented line",
        '"""',
        "    y = 1",
    ]


def test_compile_notebook_returns_line_map():
    compiler = NotebookCompiler()
    with open("jupyter/parse_example.ipynb", "r") as ntbf:
        ntb = json.load(ntbf)
    line_map = compiler.compile_notebook(ntb, "jupyter/tmp.py")
    assert isinstance(line_map, dict)
    assert len(line_map) > 0
    for output_line, (cell_num, cell_line) in line_map.items():
        assert isinstance(output_line, int)
        assert isinstance(cell_num, int)
        assert isinstance(cell_line, int)
        assert cell_num >= 1
        assert cell_line >= 1


def test_rewrite_traceback_string_matching():
    line_map = {10: (3, 5), 15: (4, 2)}
    compiled_path = "/tmp/abc123/autopipeline_tmp.py"
    notebook_path = "my_notebook.ipynb"
    tb_text = (
        'Traceback (most recent call last):\n'
        '  File "/tmp/abc123/autopipeline_tmp.py", line 10, in processor_internal\n'
        '    x = event["missing_key"]\n'
        'KeyError: \'missing_key\'\n'
    )
    result = rewrite_traceback_string(tb_text, compiled_path, notebook_path, line_map)
    assert 'File "my_notebook.ipynb", cell 3, line 5' in result
    assert "autopipeline_tmp.py" not in result


def test_rewrite_traceback_string_no_match():
    line_map = {10: (3, 5)}
    compiled_path = "/tmp/abc123/autopipeline_tmp.py"
    notebook_path = "my_notebook.ipynb"
    tb_text = (
        'Traceback (most recent call last):\n'
        '  File "/some/other/file.py", line 42, in some_func\n'
        '    raise ValueError("bad")\n'
        'ValueError: bad\n'
    )
    result = rewrite_traceback_string(tb_text, compiled_path, notebook_path, line_map)
    assert result == tb_text


def test_rewrite_traceback_string_unmapped_line():
    line_map = {10: (3, 5)}
    compiled_path = "/tmp/abc123/autopipeline_tmp.py"
    notebook_path = "my_notebook.ipynb"
    tb_text = (
        '  File "/tmp/abc123/autopipeline_tmp.py", line 999, in foo\n'
    )
    result = rewrite_traceback_string(tb_text, compiled_path, notebook_path, line_map)
    assert "autopipeline_tmp.py" in result
    assert "line 999" in result
