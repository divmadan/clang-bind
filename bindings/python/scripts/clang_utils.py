import inspect
import clang.cindex as clang


def getmembers_static(object, predicate=None):
    """
    Return all members of an object as (name, value) pairs sorted by name.
    Optionally, only return members that satisfy a given predicate.
    """

    """
    - `getmembers` function (from the inspect module) triggers execution instead of doing static analysis.
    - This leads to errors, particularly on properties of classes in cindex.py, which causes segmentation errors or raises an Exception if a particular condition is not satisfied.
    - To curb this, we need a fetch the members statically.
    - The inspect module doesn't provide a function to do so. So we define a custom function based on the one in the inspect module.
    
    diff: We replace the `getattr` function call with a `getattr_static` function call in the function definition.
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


class ClangUtils:
    """
    Clang's cindex class utilities.

    Supports the following objects:
        CursorKind:
            - A CursorKind describes the kind of entity that a cursor points to.
            - https://github.com/llvm/llvm-project/blob/1acd9a1a29ac30044ecefb6613485d5d168f66ca/clang/bindings/python/clang/cindex.py#L657
        Cursor:
            - The Cursor class represents a reference to an element within the AST. It acts as a kind of iterator.
            - https://github.com/llvm/llvm-project/blob/1acd9a1a29ac30044ecefb6613485d5d168f66ca/clang/bindings/python/clang/cindex.py#L1415
        Type:
            - The Type class represents the type of an element in the abstract syntax tree.
            - https://github.com/llvm/llvm-project/blob/1acd9a1a29ac30044ecefb6613485d5d168f66ca/clang/bindings/python/clang/cindex.py#L2180
    """

    def __init__(self, object):
        if not (
            isinstance(object, clang.CursorKind)
            or isinstance(object, clang.Cursor)
            or isinstance(object, clang.Type)
        ):
            raise NotImplementedError(f"Not implemented for {object}")

        self.check_functions_dict = {}
        self.get_functions_dict = {}
        self.properties_dict = {}

        # A list to ignore the functions/properties that causes segmentation errors.
        ignore_list = [
            "mangled_name",
            "get_address_space",
            "get_typedef_name",
            "tls_kind",
        ]

        # populate dicts
        for entry in getmembers_static(object):
            if entry[0] not in ignore_list:
                if inspect.isfunction(entry[1]):  # if function
                    try:
                        if entry[0].startswith("is_"):
                            self.check_functions_dict[entry[0]] = entry[1](object)
                        if entry[0].startswith("get_"):
                            self.get_functions_dict[entry[0]] = entry[1](object)
                    except:
                        continue
                else:  # else, property
                    try:
                        if isinstance(entry[1], property):
                            self.properties_dict[entry[0]] = getattr(object, entry[0])
                    except:
                        continue

    def get_check_functions_dict(self):
        """
        Returns: `check_functions_dict`:
            - functions that begin with "is_" i.e., checking functions
            - {function_name, function_result}
        """
        return self.check_functions_dict

    def get_get_functions_dict(self):
        """
        Returns: `get_functions_dict`:
            - functions that begin with "get_" i.e., getter functions
            - {function_name, function_result}
        """
        return self.get_functions_dict

    def get_properties_dict(self):
        """
        Returns: properties_dict
            - Properties
            - {property_name, property}
        """
        return self.properties_dict
