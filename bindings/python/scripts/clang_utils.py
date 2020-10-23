import inspect
import clang.cindex as clang


class ClangUtils:
    """
    Utilities for some classes in `cindex.py`
    """

    class CursorKindUtils:
        """
        CursorKind utilities

        `check_functions`:
            - Functions that begin with "is_" i.e., checking functions
            - A list of two-tuples: (function_name: str, function_signature: function)
        `get_functions`:
            - Functions that begin with "get_" i.e., getter functions
            - A list of two-tuples: (function_name: str, function_signature: function)
        `properties`:
            - @property functions
            - A list of two-tuples: (function_name: str, function_signature: property)
        """

        check_functions = [
            entry
            for entry in inspect.getmembers(
                clang.CursorKind, predicate=inspect.isfunction
            )
            if entry[0].startswith("is_")
        ]

        get_functions = [
            entry
            for entry in inspect.getmembers(
                clang.CursorKind, predicate=inspect.isfunction
            )
            if entry[0].startswith("get_")
        ]
        properties = [
            entry
            for entry in inspect.getmembers(clang.CursorKind)
            if isinstance(entry[1], property)
        ]

    class CursorUtils:
        """
        Cursor utilities

        `check_functions`:
            - Functions that begin with "is_" i.e., checking functions
            - A list of two-tuples: (function_name: str, function_signature: function)
        `get_functions`:
            - Functions that begin with "get_" i.e., getter functions
            - A list of two-tuples: (function_name: str, function_signature: function)
        `properties`:
            - @property functions
            - A list of two-tuples: (function_name: str, function_signature: property)
        """

        check_functions = [
            entry
            for entry in inspect.getmembers(clang.Cursor, predicate=inspect.isfunction)
            if entry[0].startswith("is_")
        ]
        get_functions = [
            entry
            for entry in inspect.getmembers(clang.Cursor, predicate=inspect.isfunction)
            if entry[0].startswith("get_")
        ]
        properties = [
            entry
            for entry in inspect.getmembers(clang.Cursor)
            if isinstance(entry[1], property)
        ]

    class TypeUtils:
        """
        Type utilities

        `check_functions`:
            - Functions that begin with "is_" i.e., checking functions
            - A list of two-tuples: (function_name: str, function_signature: function)
        `get_functions`:
            - Functions that begin with "get_" i.e., getter functions
            - A list of two-tuples: (function_name: str, function_signature: function)
        `properties`:
            - @property functions
            - A list of two-tuples: (function_name: str, function_signature: property)
        """

        check_functions = [
            entry
            for entry in inspect.getmembers(clang.Type, predicate=inspect.isfunction)
            if entry[0].startswith("is_")
        ]
        get_functions = [
            entry
            for entry in inspect.getmembers(clang.Type, predicate=inspect.isfunction)
            if entry[0].startswith("get_")
        ]
        properties = [
            entry
            for entry in inspect.getmembers(clang.Type)
            if isinstance(entry[1], property)
        ]

    class BaseEnumerationAsBase:
        """
        BaseEnumeration's derived classes' utilities

        `class_list`:
            - Classes that have class `BaseEnumeration` as their base classes
            - A list of two-tuples: (class_name: str, class_type: type)
        """

        class_list = [
            entry
            for entry in inspect.getmembers(clang, predicate=inspect.isclass)
            if entry[1].__base__ == clang.BaseEnumeration
        ]

    class StructureAsBase:
        """
        Structure's derived classes' utilities

        `class_list`:
            - Classes that have class `Structure` as their base classes
            - A list of two-tuples: (class_name: str, class_type: type)
        """

        class_list = [
            entry
            for entry in inspect.getmembers(clang, predicate=inspect.isclass)
            if entry[1].__base__ == clang.Structure
        ]
