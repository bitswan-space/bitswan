import ast
import re
import markdown

config = None
__bitswan_dev = False
__bs_step_locals = {}


def contains_function_call(ast_tree, function_name):
    for node in ast.walk(ast_tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == function_name:
                return True
    return False


def indent_code(lines: list[str] | str, indent: str = "    ", handle_multiline_quotes: bool = True) -> list[str] | str:
    is_string = isinstance(lines, str)
    if is_string:
        lines = lines.split('\n')
    
    if not handle_multiline_quotes:
        lines_out = []
        for line in lines:
            if line.strip():
                lines_out.append(indent + line)
            else:
                lines_out.append(line)
    else:
        multiline_quote_string = None
        indent_lines = []
        for i, line in enumerate(lines):
            if not multiline_quote_string and line.strip(" ") != "":
                indent_lines.append(i)
            if multiline_quote_string and multiline_quote_string in line:
                multiline_quote_string = None
                continue
            if line.count('"""') % 2 == 1:
                multiline_quote_string = '"""'
            if line.count("'''") % 2 == 1:
                multiline_quote_string = "'''"
        
        lines_out = []
        for i in range(len(lines)):
            _indent = indent if i in indent_lines else ""
            lines_out.append(_indent + lines[i])
    
    if is_string:
        return '\n'.join(lines_out)
    return lines_out


def detect_webchat(ntb):
    """
    First pass: check if any code cell contains create_webchat_flow()
    """
    for cell in ntb["cells"]:
        if cell["cell_type"] != "code":
            continue
        source = cell["source"]
        if isinstance(source, list):
            source = "".join(source)
        if not source.strip():
            continue

        try:
            parsed_ast = ast.parse(source)
        except SyntaxError:
            continue

        if contains_function_call(parsed_ast, "create_webchat_flow"):
            return True

    return False

def split_cell_on_create_webchat_flow(cell):
    """Split a notebook cell into multiple smaller cells based on *calls* to `create_webchat_flow()`."""
    source = "".join(cell["source"])
    try:
        parsed = ast.parse(source)
    except SyntaxError:
        return [cell]

    create_lines = []
    for node in ast.walk(parsed):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "create_webchat_flow"
        ):
            create_lines.append(node.lineno)

    if not create_lines:
        # No actual calls found (e.g., only imported) → keep original
        return [cell]

    create_lines.sort()
    lines = source.splitlines(keepends=True)
    split_cells = []

    # Add code before first call if exists
    if create_lines[0] > 1:
        before_lines = lines[: create_lines[0] - 1]
        if before_lines and any(line.strip() for line in before_lines):
            c1 = cell.copy()
            c1["source"] = before_lines
            split_cells.append(c1)

    # Split for each call section
    for i, start_lineno in enumerate(create_lines):
        start = start_lineno - 1
        end = create_lines[i + 1] - 1 if i + 1 < len(create_lines) else len(lines)
        chunk = lines[start:end]
        if chunk and any(line.strip() for line in chunk):
            c = cell.copy()
            c["source"] = chunk
            split_cells.append(c)

    return split_cells

class NotebookCompiler:
    _in_autopipeline = False
    _in_webchat_context = False
    _cell_number: int = 0
    _cell_processor_contents: dict[int, str] = {}
    _webchat_flows: dict[str, str] = {}
    _current_flow_name: str | None = None
    _current_chat_name: str | None = None
    _webchat_detected = False
    _auto_pipeline_added = False

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
                parsed_ast = ast.parse(clean_code)

                # Check if auto_pipeline hasn't been added and if we are in the cells that initialized webchat
                if not self._in_autopipeline and self._webchat_detected and contains_function_call(parsed_ast, "run_flow"):
                    self._in_autopipeline = True
                    pipeline_setup = """from bspump.http_webchat.server import *
from bspump.http_webchat.webchat import *
from bspump.jupyter import *

# Auto-generated pipeline setup for webchat
auto_pipeline(
    source=lambda app, pipeline: WebChatSource(app, pipeline),
    sink=lambda app, pipeline: WebchatSink(app, pipeline),
    name="WebChatPipeline"
)

"""
                    fout.write(pipeline_setup)
                    self._in_webchat_context = True

                # Check if the cell contains create_webchat_flow - so it initialize new webchat flow
                if contains_function_call(parsed_ast, "create_webchat_flow"):
                    self._webchat_detected = True

                    for node in ast.walk(parsed_ast):
                        if isinstance(node, ast.Assign):
                            for target in node.targets:
                                if isinstance(target, ast.Name):
                                    variable_name = target.id
                                    if (
                                        isinstance(node.value, ast.Call)
                                        and isinstance(node.value.func, ast.Name)
                                        and node.value.func.id == "create_webchat_flow"
                                    ):
                                        if node.value.args:
                                            arg0 = node.value.args[0]

                                            if isinstance(arg0, ast.Constant):
                                                flow_name = arg0.value
                                            elif isinstance(arg0, ast.Name):
                                                flow_name = arg0.id
                                            else:
                                                flow_name = str(self._cell_number)
                                            self._current_flow_name = flow_name
                                            self._current_chat_name = variable_name
                                            self._webchat_flows[
                                                flow_name
                                            ] = f"""
@create_webchat_flow('{flow_name}')\nasync def {flow_name}({variable_name}):\n"""


                # Check if we are still in webchat_flow code
                if self._current_flow_name:
                    cleaned_lines = [
                        line
                        for line in clean_code.split("\n")
                        if line.strip() != "" 
                        and not line.strip().startswith("#")
                        and not re.search(r'\w+\s*=\s*create_webchat_flow\s*\(', line)
                    ]
                    if cleaned_lines:
                        cleaned_code = "\n".join(cleaned_lines)
                        self._webchat_flows[self._current_flow_name] += (
                            "\n".join(indent_code(cleaned_code.split("\n"))) + "\n\n"
                        )
                    return

                # Handle regular code cells
                if not self._in_autopipeline:
                    fout.write(clean_code + "\n\n")
                else:
                    # Store code without extra indentation - it will be indented when inserted into function body
                    self._cell_processor_contents[self._cell_number] = (
                        clean_code + "\n\n"
                    )

                # Mark that we are in auto_pipeline - the following code will be added to async_step
                if not self._in_autopipeline and contains_function_call(
                    parsed_ast, "auto_pipeline"
                ):
                    self._in_autopipeline = True

        elif (
            cell["cell_type"] == "markdown"
            and self._webchat_detected
            and self._current_chat_name is not None
        ):
            markdown_content = cell["source"]
            if isinstance(markdown_content, list):
                markdown_content = "".join(markdown_content)
            markdown_content = markdown_content.strip()
            if markdown_content:
                if self._current_flow_name is not None or (
                    self._in_autopipeline and self._in_webchat_context
                ):
                    html_content = markdown.markdown(
                        markdown_content,
                        extensions=["fenced_code", "tables", "codehilite"],
                    )
                    escaped_html = html_content.replace('"', '\\"').replace("'", "\\'")
                    response_code = f'await {self._current_chat_name}.tell_user(f"""{escaped_html}""", is_html=True)\n'

                    if self._current_flow_name is not None:
                        # For webchat flows, add indentation (function body indentation)
                        self._webchat_flows[self._current_flow_name] += '    ' + response_code
                    elif self._in_autopipeline and self._in_webchat_context:
                        # For processor contents, don't indent here - will be indented when inserted
                        self._cell_processor_contents[self._cell_number] = response_code

    def compile_notebook(self, ntb, out_path="tmp.py"):
        self._cell_number = 0
        self._in_autopipeline = False
        self._in_webchat_context = False
        self._cell_processor_contents = {}
        self._current_flow_name = None
        self._current_chat_name = None
        self._webchat_detected = detect_webchat(ntb)

        with open(out_path, "w") as f:

            for cell in ntb["cells"]:
                if cell["cell_type"] == "code" and "create_webchat_flow" in "".join(cell["source"]):
                    split_cells = split_cell_on_create_webchat_flow(cell)
                    for subcell in split_cells:
                        self._cell_number += 1
                        self.parse_cell(subcell, f)
                else:
                    self._cell_number += 1
                    self.parse_cell(cell, f)


            all_contents = ''.join(self._cell_processor_contents.values())
            indented_contents = indent_code(all_contents, indent="    ", handle_multiline_quotes=False)
            
            step_func_code = f"""@async_step
async def processor_internal(inject, event):
{indented_contents}    await inject(event)

"""
            f.write(step_func_code)
            for flow_name, steps in self._webchat_flows.items():
                f.write(steps + "\n")

        # 👇 Print out the generated tmp.py content for debugging
        print("======= GENERATED PIPELINE FILE =======")
        with open(out_path, "r") as debug_f:
            print(debug_f.read())
        print("======================================")
