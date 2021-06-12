import clang.cindex as clang

from context import scripts
from scripts.clang_utils import ClangUtils
from treelib import Tree


class ParsedNode:
    def __init__(self, clang_cursor):
        self.clang_cursor = clang_cursor
        self.line = clang_cursor.location.line
        self.column = clang_cursor.location.column
        self.tokens = [x.spelling for x in clang_cursor.get_tokens()]

        # checks available in cindex.py via clang_utils.py
        self.cursor_kind = ClangUtils(clang_cursor.kind).get_all_functions_dict()
        self.cursor = ClangUtils(clang_cursor).get_all_functions_dict()
        self.type = ClangUtils(clang_cursor.type).get_all_functions_dict()

        # HACKY FIXES
        # get spelling from object
        self.cursor["result_type"] = self.cursor["result_type"].spelling
        # replace `AccessSpecifier.value` with just `value`
        self.cursor["access_specifier"] = self.cursor["access_specifier"].name
        # replace `TypeKind.value` with just `value`
        self.type["kind"] = self.type["kind"].name



class Parse:
    """
    Class containing functions to generate an AST of a file and parse it to retrieve relevant information.
    """

    def __init__(self, file, compiler_arguments):
        index = clang.Index.create()
        """
        - Why parse using the option `PARSE_DETAILED_PROCESSING_RECORD`?
            - Indicates that the parser should construct a detailed preprocessing record, 
            including all macro definitions and instantiations
            - Required to retrieve `CursorKind.INCLUSION_DIRECTIVE`
        """
        source_ast = index.parse(
            path=file,
            args=compiler_arguments,
            options=clang.TranslationUnit.PARSE_DETAILED_PROCESSING_RECORD,
        )

        self.filename = source_ast.spelling
        clang_cursor = source_ast.cursor

        self.tree = Tree()
        root_node = self.tree.create_node(
            tag=(clang_cursor.kind, clang_cursor.spelling),
            data=ParsedNode(source_ast.cursor),
        )

        self._construct_tree(root_node)

    def _is_valid_child(self, clang_child_cursor):
        """
        Check if the child is valid (child should be in the same file as the parent).
        """
        return (
            clang_child_cursor.location.file
            and clang_child_cursor.location.file.name == self.filename
        )

    def _construct_tree(self, node):
        """
        Recursively generates tree by traversing the AST of the node.
        """

        # clang_cursor = node.data.get("clang_cursor")
        clang_cursor = node.data.clang_cursor

        for clang_child_cursor in clang_cursor.get_children():
            if self._is_valid_child(clang_child_cursor):
                child_node = self.tree.create_node(
                    tag=(clang_child_cursor.kind, clang_child_cursor.spelling),
                    parent=node,
                    data=ParsedNode(clang_child_cursor),
                )
                self._construct_tree(child_node)

    def get_tree(self):
        """
        Returns the constructed tree.
        """
        return self.tree
