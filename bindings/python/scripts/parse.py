import os
import sys
import clang.cindex as clang

from context import scripts
import scripts.utils as utils
from scripts.clang_utils import ClangUtils


def valid_children(node):
    """
    A generator function yielding valid children nodes

    Parameters:
        - node (dict):
            - The node in the AST
            - Keys:
                - cursor: The cursor pointing to a node
                - filename:
                    - The file's name to check if the node belongs to it
                    - Needed to ensure that only symbols belonging to the file gets parsed, not the included files' symbols
                - depth: The depth of the node (root=0)

    Yields:
        - child_node (dict): Same structure as the argument
    """

    cursor = node["cursor"]
    filename = node["filename"]
    depth = node["depth"]

    for child in cursor.get_children():
        child_node = {"cursor": child, "filename": filename, "depth": depth + 1}
        # Check if the child belongs to the file
        if child.location.file and child.location.file.name == filename:
            yield (child_node)


def generate_parsed_info(node):
    """
    Generates parsed information by recursively traversing the AST

    Parameters:
        - node (dict):
            - The node in the AST
            - Keys:
                - cursor: The cursor pointing to a node
                - filename:
                    - The file's name to check if the node belongs to it
                    - Needed to ensure that only symbols belonging to the file gets parsed, not the included files' symbols
                - depth: The depth of the node (root=0)

    Returns:
        - parsed_info (dict):
            - Contains key-value pairs of various traits of a node
            - The key 'members' contains the node's children's `parsed_info`
    """

    cursor = node["cursor"]

    # Objects to get various kinds of checks available in cindex.py via clang_utils.py
    cursor_kind_utils = ClangUtils(cursor.kind)
    cursor_utils = ClangUtils(cursor)
    cursor_type_utils = ClangUtils(cursor.type)

    parsed_info = {
        "depth": node["depth"],
        "line": cursor.location.line,
        "column": cursor.location.column,
        "tokens": [x.spelling for x in cursor.get_tokens()],
        "cursor_kind": {
            **cursor_kind_utils.get_check_functions_dict(),  # Functions that begin with "is_" i.e., checking functions
            **cursor_kind_utils.get_get_functions_dict(),  # Functions that begin with "get_" i.e., getter functions
            **cursor_kind_utils.get_properties_dict(),  # Properties
        },
        "cursor": {
            **cursor_utils.get_check_functions_dict(),
            **cursor_utils.get_get_functions_dict(),
            **cursor_utils.get_properties_dict(),
        },
        "type": {
            **cursor_type_utils.get_check_functions_dict(),
            **cursor_type_utils.get_get_functions_dict(),
            **cursor_type_utils.get_properties_dict(),
        },
        "members": [],
    }

    # HACKY FIXES
    # get spelling from object
    parsed_info["cursor"]["result_type"] = parsed_info["cursor"]["result_type"].spelling
    # replace `AccessSpecifier.value` with just `value`
    parsed_info["cursor"]["access_specifier"] = parsed_info["cursor"][
        "access_specifier"
    ].name
    # replace `TypeKind.value` with just `value`
    parsed_info["type"]["kind"] = parsed_info["type"]["kind"].name

    # Get cursor's children and recursively add their info to a dictionary, as members of the parent
    for child_node in valid_children(node):
        child_parsed_info = generate_parsed_info(child_node)
        parsed_info["members"].append(child_parsed_info)

    return parsed_info


def get_compilation_arguments(compilation_database_path, filename):
    """
    Yields the compilation commands extracted from the compilation database

    Parameters:
        - compilation_database_path: The path to `compile_commands.json`
        - filename: The file's name to get its compilation commands

    Yields:
        - compilation commands (list): The arguments passed to the compiler
    """

    # Build a compilation database found in the given directory
    compilation_database = clang.CompilationDatabase.fromDirectory(
        buildDir=compilation_database_path
    )
    # Get compilation commands from the compilation database for the given file
    compilation_commands = compilation_database.getCompileCommands(filename=filename)

    for compilation_command in compilation_commands:
        # Extract compiler arguments, excluding compiler and filename
        yield list(compilation_command.arguments)[1:-1]


def parse_file(source, compilation_database_path=None):
    """
    Returns the parsed_info for a file

    Parameters:
        - source: Source to parse
        - compilation_database_path: The path to `compile_commands.json`

    Returns:
        - parsed_info (dict)
    """

    # Create a new index to start parsing
    index = clang.Index.create()

    # Get compiler arguments
    compiler_arguments = next(
        get_compilation_arguments(
            compilation_database_path=compilation_database_path,
            filename=source,
        )
    )

    """
    - Parse the given source code file by running clang and generating the AST before loading
    - option `PARSE_DETAILED_PROCESSING_RECORD`:
        - Indicates that the parser should construct a detailed preprocessing record, 
          including all macro definitions and instantiations.
        - Required to get the `INCLUSION_DIRECTIVE`s.
    """
    source_ast = index.parse(
        path=source,
        args=compiler_arguments,
        options=clang.TranslationUnit.PARSE_DETAILED_PROCESSING_RECORD,
    )

    # Dictionary to hold a node's information
    root_node = {
        "cursor": source_ast.cursor,
        "filename": source_ast.spelling,
        "depth": 0,
    }

    return generate_parsed_info(root_node)


def main():
    # Get command line arguments
    args = utils.parse_arguments(script="parse")
    for source in args.files:
        source = utils.get_realpath(path=source)

        # Parse the source file
        parsed_info = parse_file(source, args.compilation_database_path)

        # Output path for dumping the parsed info into a json file
        output_dir = utils.join_path(args.json_output_path, "json")
        output_filepath = utils.get_output_path(
            source=source,
            output_dir=output_dir,
            split_from=args.project_root,
            extension=".json",
        )
        out_rel_path = os.path.relpath(output_filepath, args.json_output_path)
        print(f"Producing ./{out_rel_path}")

        # Dump the parsed info at output path
        utils.dump_json(filepath=output_filepath, info=parsed_info)


if __name__ == "__main__":
    main()
