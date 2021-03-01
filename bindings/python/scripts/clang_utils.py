import inspect
import clang.cindex as clang


def getmembers_static(object, predicate=None):
    """
    Return all members of an object as (name, value) pairs sorted by name.
    Optionally, only return members that satisfy a given predicate.
    """

    """
    - `getmembers` from the inspect module triggers execution, which leads to errors when types are not satisfied.
    - So we define a custom function based on the one in the inspect module.
    - It replaces `getattr_static` with `getattr_static` to solve the issue.
    """

    if inspect.isclass(object):
        mro = (object,) + inspect.getmro(object)
    else:
        mro = ()
    results = []
    processed = set()
    names = dir(object)
    # :dd any DynamicClassAttributes to the list of names if object is a class;
    # this may result in duplicate entries if, for example, a virtual
    # attribute with the same name as a DynamicClassAttribute exists
    try:
        for base in object.__bases__:
            for k, v in base.__dict__.items():
                if isinstance(v, types.DynamicClassAttribute):
                    names.append(k)
    except AttributeError:
        pass
    for key in names:
        # First try to get the value via getattr.  Some descriptors don't
        # like calling their __get__ (see bug #1785), so fall back to
        # looking in the __dict__.
        try:
            value = inspect.getattr_static(object, key)
            # handle the duplicate key
            if key in processed:
                raise AttributeError
        except AttributeError:
            for base in mro:
                if key in base.__dict__:
                    value = base.__dict__[key]
                    break
            else:
                # could be a (currently) missing slot member, or a buggy
                # __dir__; discard and move on
                continue
        if not predicate or predicate(value):
            results.append((key, value))
        processed.add(key)
    results.sort(key=lambda pair: pair[0])
    return results


def define_class_using_macro(instance, object):
    instance.check_functions_dict = {}
    instance.get_functions_dict = {}
    instance.properties_dict = {}

    # A list to ignore the functions/properties that causes segmentation errors.
    ignore_list = ["mangled_name", "get_address_space", "get_typedef_name", "tls_kind"]

    for entry in getmembers_static(object, predicate=inspect.isfunction):
        if entry[0] not in ignore_list:
            try:
                if entry[0].startswith("is_"):
                    instance.check_functions_dict[entry[0]] = entry[1](object)
            except:
                continue
            try:
                if entry[0].startswith("get_"):
                    instance.get_functions_dict[entry[0]] = entry[1](object)
            except:
                continue

    for entry in getmembers_static(object):
        if entry[0] not in ignore_list:
            try:
                if isinstance(entry[1], property):
                    instance.properties_dict[entry[0]] = getattr(object, entry[0])
            except:
                continue


class CursorKindUtils:
    def __init__(self, cursor_kind: clang.CursorKind):
        define_class_using_macro(instance=self, object=cursor_kind)


class CursorUtils:
    def __init__(self, cursor: clang.Cursor):
        define_class_using_macro(instance=self, object=cursor)


class TypeUtils:
    def __init__(self, cursor_type: clang.Type):
        define_class_using_macro(instance=self, object=cursor_type)


# Docstring template for the classes
class_docstring = """
{class_name} class utilities

`check_functions_dict`:
    - Functions that begin with "is_" i.e., checking functions
    - A list of two-tuples: (function_name: str, function_value: function)
`get_functions_dict`:
    - Functions that begin with "get_" i.e., getter functions
    - A list of two-tuples: (function_name: str, function_value: function)
`properties_dict`:
    - @property functions
    - A list of two-tuples: (property_name: str, property_value: property)
"""

CursorKindUtils.__doc__ = class_docstring.format(class_name="CursorKind")
CursorUtils.__doc__ = class_docstring.format(class_name="Cursor")
TypeUtils.__doc__ = class_docstring.format(class_name="Type")
