import json


js_import_binding = "SplashKitBackendWASM."


name_converter = {"point_2d": "Point2D", "drawing_dest": "DrawingDest", "animation": "Animation", "vector_2d": "Vector2D", "circle": "Circle", "quad": "Quad", "color": "Color", "drawing_options": "DrawingOptions", "line": "Line", "rectangle": "Rectangle", "triangle": 'Triangle', "matrix_2d" :"Matrix2D", "resource_kind" :"ResourceKind"}

raspberry_pi = ["GpioPin", "GpioPinValue"]


class StructOSaurusRex():
    def convert_type(self, type):
        global name_converter
        swappable_names = name_converter.keys()
        if type in swappable_names:
            return name_converter[type]
        else:
            return type

    def strip_types(self, method_text):
        global name_converter
        output = method_text
        standard_type = ["int", "double", "string"]
        for name in name_converter.keys():
            if self.convert_type(name) in output:
                output = output.replace(self.convert_type(name), "")
        
        for type in standard_type:
            if type in output:
                output = output.replace(type, "")
        
        return output

    # Input example data[types][structs]
    def get_struct_name(self, line, struct_index):
        struct_name = self.convert_type(line[struct_index]["name"])
        print("Struct name: " + struct_name)
        signature = "public struct " + struct_name + " {\n\n"
        properties = ""
        for attribute in line[struct_index]["fields"].keys():
            properties += "       public "
            print("==== name: " + attribute + " ======")
            if line[struct_index]["fields"][attribute]["is_const"] == "true":
                properties += "const "

            properties += self.convert_type(line[struct_index]["fields"][attribute]["type"])

            if "void" in properties:
                properties = properties.replace("void", "IntPtr")

            if line[struct_index]["fields"][attribute]["is_array"]:
                properties += "[] "
            else:
                properties += " "
                            
            properties += attribute.capitalize() + ";\n"
        
        return struct_name, signature, properties

    # Input example data[types][structs]
    def get_struct_methods(self, line, struct_name, struct_index):
        # Code to get methods
        method_signature = ""
        method_name = ""
        method_index = 0
        methods = ""
        while method_index < len(line[struct_index]["methods"]):
            for method in line[struct_index]["methods"][method_index]["signatures"]["csharp"]:
                # Apply simple change if thing is struct.method
                if struct_name + "." in method:
                    method_signature = method.replace(struct_name + ".", "")
                    method_signature = method_signature[:-1]
                    method_signature = "      " + method_signature
                    methods += method_signature + "{\n"
                # Find method struct.method calls
                else: 
                    # Get the class the method is from
                    classes_string = method.split(".")
                    index = len(classes_string[0]) -1
                    class_name = ""
                    while index > 0:
                        if classes_string[0][index] == " ":
                            break
                        class_name += classes_string[0][index]
                        index -= 1
                    class_name = class_name[::-1]
                    # Resassemble the method name
                    method_name = class_name + "." + classes_string[1]
                    # Remove the semi colon from the end
                    # Determine if a struct val needs to be replaced by struct this
                    run_check = True
                    target = 0
                    if " " + struct_name + " " in method_name:
                        target = method_name.index(" " + struct_name + " ")
                    elif "(" + struct_name + " " in method:
                        target = method_name.index("(" + struct_name + " ")
                    else:
                        run_check = False
                    
                    #Replace struct val with struct this
                    removal_string = ""
                    while target < len(method_name) and run_check:
                        if method_name[target] == ")" or method_name[target] == ",":
                            break
                        removal_string += method_name[target]
                        target += 1
                    if run_check:
                        method_name = method_name.replace(removal_string, " " + struct_name + " this")
                    method_name = self.strip_types(method_name)
                    methods += "            " + method_name + "\n}\n"
                    
            method_index += 1
        return methods


def get_enum(line, enum_index):
    print(line[enum_index]["name"])
    enum_values = line[enum_index]["signatures"]["csharp"].split(",")

    print(enum_values)

    first = enum_values[0]
    first = first[first.index("{") + 1:]

    last = enum_values[len(enum_values) -1]
    last = last[:-1]
    enum_values[0] = " " + first
    enum_values[len(enum_values) -1] = last
    enum_name = first.split(".")[0]
    enum = "public enum " + enum_name + "{ \n"

    for value in enum_values:
        enum += value.split(".")[1] + ",\n"

    enum += "}\n"

    return enum


struct_data = StructOSaurusRex()

def get_function_this(line):
    definition = line.split(".")
    #Define Function
    fun = definition[1]
    start = fun.index("(")
    fun = fun[:start]
    fun += "(this);"; 
    fun = "SplashKit." + fun
    return fun

function_objects = []


def get_bindings(line):
    global maps
    cpp_name = line["name"]

    for definition in line["signatures"]["csharp"]:
        fun_getter = False

        if " { get }" in definition:
            fun_getter = True

        if "uint" in definition:
            continue

        signature = {
            "function_definition": "",
            "function_to_bind": cpp_name
            }
        
        function_definition = ""

        if "static" in definition and not fun_getter:
            location = definition.index("static") + len("static")
            part_two = definition[location:]
            part_one = definition[:location]
            function_definition = part_one + " partial" + part_two
        elif not fun_getter:
            location = definition.index("public") + len("static")
            part_two = definition[location:]
            part_one = definition[:location]
            function_definition =  part_one + " partial" + part_two

        if " { get }" in definition:
            fun_to_get = get_function_this(line["signatures"]["csharp"][1])
            function_definition = function_definition.replace(" { get }", "{ get => " + fun_to_get + " }")
            signature["function_to_bind"] = False

        if " { set }" in definition:
            continue
            function_definition = function_definition.replace(" { set }", ";")

        if "." in definition:
            classes_string = definition.split(".")[0]
            index = len(classes_string) -1
            class_name = ""
            while index > 0:
                if classes_string[index] == " ":
                    break
                class_name += classes_string[index]
                index -= 1
            class_name = class_name[::-1]


            if class_name not in maps.keys():
                maps[class_name] = []
        else:
            continue
        
        unsupported_types = ["Connection", "Window", "Sprite", "Json", "Font", "Timer", "FreeNotifier", "AdcPin", "AdcType", "AdcDevice", "AdcDevice", "Bitmap", "WebServer", "HttpRequest", "ushort", "Message", "ServerSocket", "HttpResponse", "KeyCallback", "KeyCode", "MouseButton", "Display", "LogMode", "InterfaceStyle", "SoundEffect", "Music", "AnimationScript", " ref ", "LogLevel", "List<string>"]
        unsupported_functions = ["Assign(", "Restart(", "Update(", "Free("]
        for el in name_converter.keys():
            if name_converter[el] + " " in function_definition:
                print("Removed")
                return

        for el in unsupported_types:
            if el in function_definition:
                return
        
        for el in unsupported_functions:
            if el in function_definition:
                return
        
        # Remove raspberry pi commands
        for pi_command in raspberry_pi:
            if pi_command in function_definition:
                return

        function_definition = function_definition.replace(class_name + ".", "")

        signature["function_definition"] = function_definition

        maps[class_name].append(signature)
    



#! Program entry point

with open("./api.json") as json_data:
    data = json.load(json_data)

catergories = list(data.keys())
catergory = 0


maps = {}
structs = ""
enums = ""

while catergory < len(catergories):
    function_index = 0
    struct_index = 0
    enum_index = 0
    while function_index < len(data[catergories[catergory]]["functions"]):
        get_bindings(data[catergories[catergory]]["functions"][function_index])
        function_index += 1
    while struct_index < len(data[catergories[catergory]]["structs"]):
        print("========================")
        struct_name, signature, properties = struct_data.get_struct_name(data[catergories[catergory]]["structs"], struct_index)
        methods = struct_data.get_struct_methods(data[catergories[catergory]]["structs"], struct_name, struct_index)
        print("========================")
        if struct_name != "Color" and struct_name != "Circle":
            structs += "\n"
            structs += signature + "\n"
            structs += properties + "\n"
            structs += methods + "}\n"
        struct_index += 1
    
    while enum_index < len(data[catergories[catergory]]["enums"]):
        enums += get_enum(data[catergories[catergory]]["enums"], enum_index)
        enum_index += 1

    catergory += 1


# Output the file
output_file = open("SplashKitBindings.Generated.cs", "w")

mandatory = """\n

using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Runtime.CompilerServices;
using System.Runtime.InteropServices.JavaScript;
using __sklib_ptr = System.IntPtr;


[UnmanagedFunctionPointerAttribute(CallingConvention.Cdecl)]
public delegate void KeyCallback(int code);\n

[UnmanagedFunctionPointerAttribute(CallingConvention.Cdecl)]
public delegate void FreeNotifier(IntPtr pointer);\n

[UnmanagedFunctionPointerAttribute(CallingConvention.Cdecl)]
public delegate void SpriteEventHandler(IntPtr s, int evt);\n

[UnmanagedFunctionPointerAttribute(CallingConvention.Cdecl)]
public delegate void SpriteFloatFunction(IntPtr s, float f);\n

[UnmanagedFunctionPointerAttribute(CallingConvention.Cdecl)]
public delegate void SpriteFunction(IntPtr s);\n


"""


classes = maps.keys()
output = mandatory +" \n\nnamespace SplashKitSDK \n{\n"

classes_to_remove = ["AdcDevice", "Circle", "Color"]

for SK_class in classes:

    # remove raspberry Pi related classes
    if SK_class in classes_to_remove:
        continue

    output += "   public partial class " + SK_class + "\n   {\n"

    for definition in maps[SK_class]:



        if definition["function_to_bind"] != False:
            output += "      [JSImport(\"SplashKitBackendWASM." + definition["function_to_bind"] +"\", \"main.js\")] \n"
        output += "      " + definition["function_definition"] + "\n\n"

    output += "     } \n\n"

output += structs
output += enums
output += "} \n"


output_file.write(output)