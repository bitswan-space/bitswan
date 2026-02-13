import re
import sys
import traceback


def rewrite_traceback_string(tb_text, compiled_path, notebook_path, line_map):
    """Rewrite traceback text to reference notebook cells instead of the compiled tmp file."""
    pattern = re.compile(
        r'(File\s+")' + re.escape(compiled_path) + r'(",\s+line\s+)(\d+)'
    )

    def replacer(match):
        line_no = int(match.group(3))
        if line_no in line_map:
            cell_num, cell_line = line_map[line_no]
            return f'File "{notebook_path}", cell {cell_num}, line {cell_line}'
        return match.group(0)

    return pattern.sub(replacer, tb_text)


def install(notebook_path, compiled_path, line_map):
    """Monkey-patch traceback.format_exception and sys.excepthook for notebook-aware traces."""
    original_format_exception = traceback.format_exception

    def patched_format_exception(*args, **kwargs):
        result = original_format_exception(*args, **kwargs)
        return [
            rewrite_traceback_string(line, compiled_path, notebook_path, line_map)
            for line in result
        ]

    traceback.format_exception = patched_format_exception

    def excepthook(exc_type, exc_value, exc_tb):
        lines = patched_format_exception(exc_type, exc_value, exc_tb)
        sys.stderr.write("".join(lines))

    sys.excepthook = excepthook
