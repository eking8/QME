"""Manages app project files that should be edited."""
import pathlib


def insert_before(path, value_to_find, code_to_insert) -> str:
    """Insert code before any occurrence of value.

    Args:
        path: Path to file
        value_to_find: search term.
        code_to_insert: Text to insert before search term.

    Returns: Text of modified file.
    """
    contents = []
    for line in path.open(mode="r"):
        if value_to_find not in line:
            contents.append(line)
            continue

        contents.append(code_to_insert)
        contents.append(line)

    return "".join(contents)


def insert_after(path, value_to_find, code_to_insert):
    """Insert code after any first of value.

    Args:
        path: Path to file
        value_to_find: search term.
        code_to_insert: Text to insert before search term.

    Returns: Text of modified file.
    """
    content = []
    added = False
    for line in path.open():
        content.append(line)
        if value_to_find in line and not added:
            content.append(code_to_insert)
            added = True

    return "".join(content)


def insert_line_at_block_end(path, block_start, line_to_insert):
    """Insert code at the end of a text block.

    Args:
        path: Path to file
        block_start: Search term that triggers the beginning of block.
        line_to_insert: Text to insert at end of block.

    Returns: Text of modified file.
    """
    contents = path.open().readlines()
    start, end = find_block_indexes(contents, block_start)

    if start and end and start != end:
        contents.insert(end, line_to_insert + "\n")

    return "".join(contents)


def add_indentation(num_indents, num_spaces=4):
    """Add indentation

    Args:
        num_indents: number of indentations
        num_spaces: Num spaces per indent. Defaults to 4.

    Returns:
        spaces
    """
    return " " * num_indents * num_spaces


def find_block_indexes(lines, key):
    """Find indices of opening and closing block.

    Note, this does not yet handle recursive blocks.

    For example:
    1  if statement1 {
    2    if statement2 {
    3    }
    4  }

    will return 1, 3.

    Args:
        lines: List of text lines.
        key: Search term which starts block.

    Returns: tuple of start and end of block.
    """
    total_lines = len(lines)
    start = None
    end = None
    for line_num in range(total_lines):
        line = lines[line_num]
        if key in line:
            for num in range(line_num, total_lines):
                line = lines[num]
                if "{" in line:
                    start = num
                if "}" in line:
                    end = num
                    break
            break
    return start, end


def insert_in_function_after_hint(
    path: pathlib.Path, function_signature_hint: str, code: str, indentation: int = 4,
):
    """Insert code in function with signature hint text in definition.

    Args:
        path: Path to code.
        function_signature_hint: text to look for in function signature.
            Should be unique.
        code: Code to insert.
        indentation: Width of indentation.

    Returns: Modified file.
    """
    found_function = False
    in_function = False
    output_lines = []
    configure_added = False
    for line in path.open():
        output_lines.append(line)

        if function_signature_hint in line:
            found_function = True

        # Searching for start of function
        if found_function and not in_function:
            if "{" in line:
                in_function = True
            continue

        if in_function and "}" in line:
            in_function = False
            continue

        if not in_function:
            continue

        if in_function and not configure_added:
            # Adding FritCore.configure
            message = "// Automatically added by fritz app setup."
            output_lines.append(" " * indentation + message + "\n")
            output_lines.append(" " * indentation + code + "\n")
            configure_added = True

    return "".join(output_lines)
