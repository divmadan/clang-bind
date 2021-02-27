from context import scripts
import clang.cindex as clang
import scripts.parse as parse


def create_compilation_database(tmp_path, filepath):
    input = tmp_path / "compile_commands.json"
    x = [
        {
            "directory": f"{tmp_path}",
            "command": f"/usr/bin/clang++ -std=c++14 {filepath}",
            "file": f"{filepath}",
        }
    ]

    with open(input, "w") as f:
        f.write(str(x))

    return str(tmp_path)


def get_parsed_info(tmp_path, file_contents):
    source_path = tmp_path / "file.cpp"

    with open(source_path, "w") as f:
        f.write(str(file_contents))

    parsed_info = parse.parse_file(
        source=str(source_path),
        compilation_database_path=create_compilation_database(
            tmp_path=tmp_path, filepath=source_path
        ),
    )

    return parsed_info


def test_anonymous_decls(tmp_path):
    file_contents = """
    union {
        struct {
            enum {};
        };
    };
    """
    parsed_info = get_parsed_info(tmp_path=tmp_path, file_contents=file_contents)

    union_decl = parsed_info["members"][0]
    print(union_decl["Cursor"])

    assert union_decl["CursorKind"]["name"] == "UNION_DECL"
    assert union_decl["Cursor"]["is_anonymous"] == True
    assert union_decl["Cursor"]["spelling"] == ""

    struct_decl = union_decl["members"][0]

    assert struct_decl["CursorKind"]["name"] == "STRUCT_DECL"
    assert union_decl["Cursor"]["is_anonymous"] == True
    assert union_decl["Cursor"]["spelling"] == ""

    enum_decl = struct_decl["members"][0]

    assert enum_decl["CursorKind"]["name"] == "ENUM_DECL"
    assert union_decl["Cursor"]["is_anonymous"] == True
    assert union_decl["Cursor"]["spelling"] == ""


def test_translation_unit(tmp_path):
    file_contents = ""
    parsed_info = get_parsed_info(tmp_path=tmp_path, file_contents=file_contents)

    assert parsed_info["CursorKind"]["name"] == "TRANSLATION_UNIT"
    assert parsed_info["depth"] == 0
    assert parsed_info["Cursor"]["spelling"] == str(tmp_path / "file.cpp")


def test_namespace(tmp_path):
    file_contents = "namespace a_namespace {}"
    parsed_info = get_parsed_info(tmp_path=tmp_path, file_contents=file_contents)

    namespace = parsed_info["members"][0]

    assert namespace["CursorKind"]["name"] == "NAMESPACE"
    assert namespace["Cursor"]["spelling"] == "a_namespace"


def test_namespace_ref(tmp_path):
    file_contents = """
    #include <ostream>
    std::ostream anOstream;
    """
    parsed_info = get_parsed_info(tmp_path=tmp_path, file_contents=file_contents)

    inclusion_directive = parsed_info["members"][0]

    assert inclusion_directive["CursorKind"]["name"] == "INCLUSION_DIRECTIVE"
    assert inclusion_directive["Cursor"]["spelling"] == "ostream"

    var_decl = parsed_info["members"][1]
    namespace_ref = var_decl["members"][0]

    assert namespace_ref["CursorKind"]["name"] == "NAMESPACE_REF"
    assert namespace_ref["Cursor"]["spelling"] == "std"


def test_var_decl(tmp_path):
    file_contents = "int anInt = 1;"
    parsed_info = get_parsed_info(tmp_path=tmp_path, file_contents=file_contents)

    var_decl = parsed_info["members"][0]

    assert var_decl["CursorKind"]["name"] == "VAR_DECL"
    assert var_decl["Type"]["kind"] == "INT"
    assert var_decl["Cursor"]["spelling"] == "anInt"


def test_field_decl(tmp_path):
    file_contents = """
    struct AStruct {
        int aClassMember;
    };
    """
    parsed_info = get_parsed_info(tmp_path=tmp_path, file_contents=file_contents)

    struct_decl = parsed_info["members"][0]
    field_decl = struct_decl["members"][0]

    assert field_decl["CursorKind"]["name"] == "FIELD_DECL"
    assert field_decl["Type"]["kind"] == "INT"
    assert field_decl["Cursor"]["spelling"] == "aClassMember"


def test_parsed_info_structure(tmp_path):
    file_contents = ""
    parsed_info = get_parsed_info(tmp_path=tmp_path, file_contents=file_contents)

    assert type(parsed_info) is dict
    assert type(parsed_info["members"]) is list
    assert len(parsed_info["members"]) == 0


def test_function_decl_without_parameters(tmp_path):
    file_contents = """
    int aFunction();
    """
    parsed_info = get_parsed_info(tmp_path=tmp_path, file_contents=file_contents)

    func_decl = parsed_info["members"][0]

    assert func_decl["CursorKind"]["name"] == "FUNCTION_DECL"
    assert func_decl["Cursor"]["spelling"] == "aFunction"
    assert func_decl["Cursor"]["result_type"] == "int"


def test_function_decl_with_parameters(tmp_path):
    file_contents = """
    int aFunction(int firstParam, double secondParam);
    """
    parsed_info = get_parsed_info(tmp_path=tmp_path, file_contents=file_contents)

    func_decl = parsed_info["members"][0]

    assert func_decl["CursorKind"]["name"] == "FUNCTION_DECL"
    assert func_decl["Cursor"]["spelling"] == "aFunction"
    assert func_decl["Cursor"]["result_type"] == "int"

    first_param = func_decl["members"][0]
    second_param = func_decl["members"][1]

    assert first_param["Cursor"]["spelling"] == "firstParam"
    assert first_param["Type"]["kind"] == "INT"

    assert second_param["Cursor"]["spelling"] == "secondParam"
    assert second_param["Type"]["kind"] == "DOUBLE"


def test_simple_call_expr(tmp_path):
    file_contents = """
    int aFunction() {
        return 1;
    }
    int anInt = aFunction();
    """
    parsed_info = get_parsed_info(tmp_path=tmp_path, file_contents=file_contents)

    var_decl = parsed_info["members"][1]
    call_expr = var_decl["members"][0]

    assert call_expr["CursorKind"]["name"] == "CALL_EXPR"
    assert call_expr["Cursor"]["spelling"] == "aFunction"

    assert var_decl["Cursor"]["spelling"] == "anInt"


def test_struct_decl(tmp_path):
    file_contents = "struct AStruct {};"
    parsed_info = get_parsed_info(tmp_path=tmp_path, file_contents=file_contents)

    struct_decl = parsed_info["members"][0]

    assert struct_decl["CursorKind"]["name"] == "STRUCT_DECL"
    assert struct_decl["Cursor"]["spelling"] == "AStruct"


def test_public_inheritance(tmp_path):
    file_contents = """
    struct BaseStruct {};
    struct DerivedStruct: public BaseStruct {};
    """
    parsed_info = get_parsed_info(tmp_path=tmp_path, file_contents=file_contents)

    child_struct_decl = parsed_info["members"][1]
    cxx_base_specifier = child_struct_decl["members"][0]

    assert cxx_base_specifier["CursorKind"]["name"] == "CXX_BASE_SPECIFIER"
    assert cxx_base_specifier["Cursor"]["access_specifier"] == "PUBLIC"
    assert cxx_base_specifier["Cursor"]["spelling"] == "struct BaseStruct"


def test_member_function(tmp_path):
    file_contents = """
    struct AStruct {
        void aMethod() {}
    };
    """
    parsed_info = get_parsed_info(tmp_path=tmp_path, file_contents=file_contents)

    struct_decl = parsed_info["members"][0]
    cxx_method = struct_decl["members"][0]

    assert cxx_method["CursorKind"]["name"] == "CXX_METHOD"
    assert cxx_method["Cursor"]["result_type"] == "void"
    assert cxx_method["Cursor"]["spelling"] == "aMethod"


def test_type_ref(tmp_path):
    file_contents = """
    struct SomeUsefulType {};

    class AClass {
        void aMethod(SomeUsefulType aParameter) {};
    };
    """
    parsed_info = get_parsed_info(tmp_path=tmp_path, file_contents=file_contents)

    class_decl = parsed_info["members"][1]
    cxx_method = class_decl["members"][0]
    parm_decl = cxx_method["members"][0]

    assert parm_decl["Cursor"]["spelling"] == "aParameter"

    type_ref = parm_decl["members"][0]

    assert type_ref["CursorKind"]["name"] == "TYPE_REF"
    assert type_ref["Cursor"]["spelling"] == "struct SomeUsefulType"


def test_simple_constructor(tmp_path):
    file_contents = """
    struct AStruct {
        AStruct() {}
    };
    """
    parsed_info = get_parsed_info(tmp_path=tmp_path, file_contents=file_contents)

    struct_decl = parsed_info["members"][0]
    constructor = struct_decl["members"][0]

    assert constructor["CursorKind"]["name"] == "CONSTRUCTOR"
    assert constructor["Cursor"]["access_specifier"] == "PUBLIC"
    assert constructor["Cursor"]["spelling"] == "AStruct"


def test_unexposed_expr(tmp_path):
    file_contents = """
    class SimpleClassWithConstructor {
        int aClassMember;
        SimpleClassWithConstructor(int aConstructorParameter) : aClassMember(aConstructorParameter) {};
    };
    """
    parsed_info = get_parsed_info(tmp_path=tmp_path, file_contents=file_contents)

    struct_decl = parsed_info["members"][0]
    constructor = struct_decl["members"][1]
    member_ref = constructor["members"][1]

    assert member_ref["Cursor"]["spelling"] == "aClassMember"

    unexposed_expr = constructor["members"][2]

    assert unexposed_expr["CursorKind"]["name"] == "UNEXPOSED_EXPR"
    assert unexposed_expr["Cursor"]["spelling"] == "aConstructorParameter"


# @TODO: Not sure how to reproduce. Maybe later.
# def test_member_ref_expr(tmp_path):


def test_decl_ref_expr(tmp_path):
    file_contents = """
    struct AStruct {
        int firstMember, secondMember;
        AStruct(int firstFunctionParameter, int secondFunctionParameter)
        : firstMember(secondFunctionParameter), secondMember(firstFunctionParameter)
        {}
    };
    """
    parsed_info = get_parsed_info(tmp_path=tmp_path, file_contents=file_contents)

    struct_decl = parsed_info["members"][0]
    constructor = struct_decl["members"][2]
    unexposed_expr_1 = constructor["members"][3]
    unexposed_expr_2 = constructor["members"][5]
    decl_ref_expr_1 = unexposed_expr_1["members"][0]
    decl_ref_expr_2 = unexposed_expr_2["members"][0]

    assert decl_ref_expr_1["CursorKind"]["name"] == "DECL_REF_EXPR"
    assert decl_ref_expr_2["CursorKind"]["name"] == "DECL_REF_EXPR"
    assert decl_ref_expr_1["Cursor"]["spelling"] == "secondFunctionParameter"
    assert decl_ref_expr_2["Cursor"]["spelling"] == "firstFunctionParameter"


def test_member_ref(tmp_path):
    file_contents = """
    struct AStruct {
        int firstMember, secondMember;
        AStruct(int firstFunctionParameter, int secondFunctionParameter)
        : firstMember(secondFunctionParameter), secondMember(firstFunctionParameter)
        {}
    };
    """
    parsed_info = get_parsed_info(tmp_path=tmp_path, file_contents=file_contents)
    struct_decl = parsed_info["members"][0]
    constructor = struct_decl["members"][2]
    member_ref_1 = constructor["members"][2]
    member_ref_2 = constructor["members"][4]

    assert member_ref_1["CursorKind"]["name"] == "MEMBER_REF"
    assert member_ref_2["CursorKind"]["name"] == "MEMBER_REF"
    assert member_ref_1["Type"]["kind"] == "INT"
    assert member_ref_2["Type"]["kind"] == "INT"
    assert member_ref_1["Cursor"]["spelling"] == "firstMember"
    assert member_ref_2["Cursor"]["spelling"] == "secondMember"


def test_class_template(tmp_path):
    file_contents = """
    template <typename T>
    struct AStruct {};
    """
    parsed_info = get_parsed_info(tmp_path=tmp_path, file_contents=file_contents)

    class_template = parsed_info["members"][0]

    assert class_template["CursorKind"]["name"] == "CLASS_TEMPLATE"
    assert class_template["Cursor"]["spelling"] == "AStruct"

    template_type_parameter = class_template["members"][0]

    assert template_type_parameter["CursorKind"]["name"] == "TEMPLATE_TYPE_PARAMETER"
    assert template_type_parameter["Cursor"]["spelling"] == "T"
    assert template_type_parameter["Cursor"]["access_specifier"] == "PUBLIC"


def test_template_non_type_parameter(tmp_path):
    file_contents = """
    template <int N>
    struct AStruct {};
    """
    parsed_info = get_parsed_info(tmp_path=tmp_path, file_contents=file_contents)

    class_template = parsed_info["members"][0]

    assert class_template["CursorKind"]["name"] == "CLASS_TEMPLATE"
    assert class_template["Cursor"]["spelling"] == "AStruct"

    template_non_type_parameter = class_template["members"][0]

    assert (
        template_non_type_parameter["CursorKind"]["name"]
        == "TEMPLATE_NON_TYPE_PARAMETER"
    )
    assert template_non_type_parameter["Type"]["kind"] == "INT"
    assert template_non_type_parameter["Cursor"]["spelling"] == "N"


def test_function_template(tmp_path):
    file_contents = """
    template <typename T>
    void aFunction() {}
    """
    parsed_info = get_parsed_info(tmp_path=tmp_path, file_contents=file_contents)

    function_template = parsed_info["members"][0]

    assert function_template["CursorKind"]["name"] == "FUNCTION_TEMPLATE"
    assert function_template["Cursor"]["result_type"] == "void"
    assert function_template["Cursor"]["spelling"] == "aFunction"

    template_type_parameter = function_template["members"][0]

    assert template_type_parameter["CursorKind"]["name"] == "TEMPLATE_TYPE_PARAMETER"
    assert template_type_parameter["Cursor"]["spelling"] == "T"
    assert template_type_parameter["Cursor"]["access_specifier"] == "PUBLIC"


def test_template_type_parameter(tmp_path):
    file_contents = """
    template <typename T>
    struct AStruct {};

    template <typename P>
    void aFunction() {}
    """
    parsed_info = get_parsed_info(tmp_path=tmp_path, file_contents=file_contents)

    class_template = parsed_info["members"][0]
    template_type_parameter = class_template["members"][0]

    assert template_type_parameter["CursorKind"]["name"] == "TEMPLATE_TYPE_PARAMETER"
    assert template_type_parameter["Type"]["kind"] == "UNEXPOSED"
    assert template_type_parameter["Cursor"]["spelling"] == "T"

    function_template = parsed_info["members"][1]
    template_type_parameter = function_template["members"][0]

    assert template_type_parameter["CursorKind"]["name"] == "TEMPLATE_TYPE_PARAMETER"
    assert template_type_parameter["Type"]["kind"] == "UNEXPOSED"
    assert template_type_parameter["Cursor"]["spelling"] == "P"


def test_default_delete_constructor(tmp_path):
    file_contents = """
    class aClass {
        aClass() = default;

        // disable the copy constructor
        aClass(double) = delete;
    };
    """
    parsed_info = get_parsed_info(tmp_path=tmp_path, file_contents=file_contents)

    class_decl = parsed_info["members"][0]

    default_constructor = class_decl["members"][0]

    assert default_constructor["CursorKind"]["name"] == "CONSTRUCTOR"
    assert default_constructor["Cursor"]["spelling"] == "aClass"
    assert default_constructor["Cursor"]["result_type"] == "void"
    assert default_constructor["Cursor"]["is_default_constructor"]

    delete_constructor = class_decl["members"][1]

    assert delete_constructor["CursorKind"]["name"] == "CONSTRUCTOR"
    assert delete_constructor["Cursor"]["spelling"] == "aClass"
    assert delete_constructor["Cursor"]["result_type"] == "void"
    # no check available for deleted ctor analogous to `is_default_constructor`
