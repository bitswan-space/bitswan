import json
import os
import ast
import sys
import tempfile
import re

from bspump.jupyter import *  # noqa: F403
import bspump.jupyter
import bspump.notebook_traceback

config = None
__bitswan_dev = False
__bs_step_locals = {}


def contains_function_call(ast_tree, function_name):
    for node in ast.walk(ast_tree):
        if isinstance(node, ast.Call):  # Check if the node is a function call
            if isinstance(node.func, ast.Name) and node.func.id == function_name:
                return True
    return False


def indent_code(lines: list[str]) -> list[str]:
    multiline = False
    double_quotes = False
    indent_lines = []
    lines_out = []
    for i, line in enumerate(lines):
        if not multiline and line.strip(" ") != "":
            indent_lines.append(i)
        for q in ('"""', "'''"):
            if q not in line:
                continue
            if not multiline:
                if line.count(q) % 2 == 1:
                    double_quotes = q == '"""'
                    multiline = True
                break
            else:
                matching = (double_quotes and q == '"""') or (
                    not double_quotes and q == "'''"
                )
                if matching and line.count(q) % 2 == 1:
                    multiline = False
                break
    for i in range(len(lines)):
        _indent = "    " if i in indent_lines else ""
        lines_out.append(_indent + lines[i])
    return lines_out


class NotebookCompiler:
    _in_autopipeline = False
    _cell_number: int = 0
    _cell_processor_contents: dict[int, tuple[str, int, int]] = {}
    _line_map: dict[int, tuple[int, int]] = {}
    _output_line: int = 0

    def parse_cell(self, cell, fout):
        if cell["cell_type"] == "code":
            source = cell["source"]
            if len(source) > 0 and "#ignore" not in source[0]:
                code = (
                    "".join(cell["source"])
                    if isinstance(cell["source"], list)
                    else cell["source"]
                )

                clean_code = (
                    "\n".join(
                        [
                            re.sub(r"^\t+(?=\S)", "", line)
                            if not line.startswith("!")
                            else ""
                            for line in code.split("\n")
                        ]
                    ).strip("\n")
                    + "\n"
                )

                if not clean_code.strip():
                    return
                if not self._in_autopipeline:
                    source_lines = clean_code.split("\n")
                    for src_line_idx, src_line in enumerate(source_lines):
                        self._output_line += 1
                        self._line_map[self._output_line] = (
                            self._cell_number,
                            src_line_idx + 1,
                        )
                    # Account for the two blank lines after
                    self._output_line += 2
                    fout.write(clean_code + "\n\n")
                else:
                    indented = "\n".join(indent_code(clean_code.split("\n"))) + "\n\n"
                    num_source_lines = len(clean_code.split("\n"))
                    self._cell_processor_contents[self._cell_number] = (
                        indented,
                        self._cell_number,
                        num_source_lines,
                    )
                if not self._in_autopipeline and contains_function_call(
                    ast.parse(clean_code), "auto_pipeline"
                ):
                    self._in_autopipeline = True

    def compile_notebook(self, ntb, out_path="tmp.py"):
        self._cell_number = 0
        self._in_autopipeline = False
        self._cell_processor_contents = {}
        self._line_map = {}
        self._output_line = 0
        with open(out_path, "w") as f:
            for cell in ntb["cells"]:
                self._cell_number += 1
                self.parse_cell(cell, f)

            # @async_step header line
            self._output_line += 1
            # async def processor_internal(...) line
            self._output_line += 1

            # Map processor body lines
            for cell_num, (indented, cell_id, num_src_lines) in self._cell_processor_contents.items():
                indented_lines = indented.split("\n")
                src_line_counter = 0
                for line_text in indented_lines:
                    self._output_line += 1
                    src_line_counter += 1
                    if src_line_counter <= num_src_lines:
                        self._line_map[self._output_line] = (
                            cell_id,
                            src_line_counter,
                        )

            # await inject(event) line
            self._output_line += 1

            step_func_code = f"""@async_step
async def processor_internal(inject, event):
{"".join(v[0] for v in self._cell_processor_contents.values())}    await inject(event)
"""
            f.write(step_func_code)

        return self._line_map


def main():
    app = App()  # noqa: F405
    compiler = NotebookCompiler()

    if app.Test:
        bspump.jupyter.bitswan_test_mode.append(True)

    with tempfile.TemporaryDirectory() as tmpdirname:
        if os.path.exists(app.Notebook):
            with open(app.Notebook) as nb:
                notebook = json.load(nb)
                compiled_path = f"{tmpdirname}/autopipeline_tmp.py"
                line_map = compiler.compile_notebook(
                    notebook, out_path=compiled_path
                )
                bspump.notebook_traceback.install(
                    app.Notebook, compiled_path, line_map
                )
                sys.path.insert(0, tmpdirname)
                tmp_module = __import__("autopipeline_tmp")  # noqa: F841
        else:
            exit(f"Notebook {app.Notebook} not found")

        if bspump.jupyter.bitswan_auto_pipeline.get("sink") is not None:
            register_sink(  # noqa: F405
                bspump.jupyter.bitswan_auto_pipeline.get("sink")
            )  # noqa: F405
            end_pipeline()  # noqa: F405

        app.init_componets()
        app.run()


if __name__ == "__main__":
    main()
