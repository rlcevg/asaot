#
# Copyright (c) 2012 Fredrik Ehnbom
#
# This software is provided 'as-is', without any express or implied
# warranty. In no event will the authors be held liable for any damages
# arising from the use of this software.
#
# Permission is granted to anyone to use this software for any purpose,
# including commercial applications, and to alter it and redistribute it
# freely, subject to the following restrictions:
#
#    1. The origin of this software must not be misrepresented; you must not
#    claim that you wrote the original software. If you use this software
#    in a product, an acknowledgment in the product documentation would be
#    appreciated but is not required.
#
#    2. Altered source versions must be plainly marked as such, and must not be
#    misrepresented as being the original software.
#
#    3. This notice may not be removed or altered from any source
#    distribution.
#/
import os
import re
import sys

out = open(sys.argv[2], "w") if len(sys.argv) > 2 else sys.stdout


def emit(line=""):
    out.write(line + "\n")


as_context_cpp = "%s/source/as_context.cpp" % sys.argv[1]
angelscript_h = "%s/include/angelscript.h" % sys.argv[1]

f = open(as_context_cpp)
data = f.read()
f.close()

data          = re.search(r"(asCContext::ExecuteNext.*?\n}\n)", data, re.DOTALL).group(1)
commentre     = re.compile(r"^\s*//")
jumpre        = re.compile(r"\s*l_bc\s*\+=[\s\d+]+asBC")
argre         = re.compile(r"(\w+ARG\w*)\(l_bc([^)]*)\)")
callscriptre  = re.compile(r"(m_regs\.stackFramePointer\s*=\s*l_fp;\s+?)"\
                           r"(.*?)([ \t]*)(Call(InterfaceMethod|ScriptFunction))\((.*?)\);(.+?)"\
                           r"(l_\w+\s+=\s*m_regs\.\w+Pointer;)[\s\n\r]+"\
                           r"(l_\w+\s+=\s*m_regs\.\w+Pointer;)[\s\n\r]+"\
                           r"(l_\w+\s+=\s*m_regs\.\w+Pointer;)[\s\n\r]+"\
                           r"((.*?if.*?)(return;))", re.DOTALL)
callsystemre2 = re.compile(r"l_sp\s*\+=\s*CallSystemFunction\(\s*(\w+)\s*,\s*(\w+)\s*\);")


retre = re.compile(r"([\t ]+)(PopCallState\(\);).*?l_sp\s*\+=\s*(.*?);", re.DOTALL)

f = open(angelscript_h)
data2 = f.read()
f.close()

data2 = data2.replace("AS_NAMESPACE_QUALIFIER ", "")
lut = dict(re.findall(r"#define\s*(asBC_\w+ARG[^\(]*)\(.*?\)\s+.*?(\w+)", data2, re.DOTALL))
def gettypename(macro):
    return lut[macro]

def gettypeprintf(macro):
    if lut[macro] == "float":
        return "%f"
    elif lut[macro] == "asQWORD":
        return "%llu"
    elif lut[macro] == "asDWORD":
        return "%lu"
    return "%d"


def parse_instructions(source):
    matches = list(re.finditer(r"^\s*INSTRUCTION\((asBC_[^)]+)\):", source, re.MULTILINE))
    instructions = []
    for idx, match in enumerate(matches):
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(source)
        body = source[start:end]
        instructions.append((match.group(1), body))
    return instructions


bytecodes = parse_instructions(data)
emit("#include <angelscript.h>")
emit("#include <as_scriptengine.h>")
emit("#include <stdio.h>")
emit("#include <assert.h>")
emit("#include <math.h>")
emit("#include <as_callfunc.h>")
emit("#include \"AOTCompiler.h\"")
emit()
emit("#define ASSERT assert")
emit("#define asASSERT(x) ")
emit("#define BUFSIZE 512 ")
emit()
emit("static unsigned int callsyscount = 0;")
emit("void AOTCompiler::ProcessByteCode(asDWORD *byteCode, asUINT offset, asEBCInstr op, AOTFunction &func)")
emit("{")
emit("    switch (op)")
emit("    {")

for bytecode in bytecodes:
    if bytecode[0] == "asBC_JitEntry":
        continue

    emit("        case %s:" % bytecode[0])
    emit("        {")
    emit("            func.m_output += \"\t\t// %s\\n\";" % bytecode[0])

    data = bytecode[1]
    data = data[:data.rfind("NEXT_INSTRUCTION();")]
    data = callscriptre.sub(r"""\1\3
\2
\3asCScriptFunction *__func = \6;
\3\4(__func);
#if %d                                                                                                                             __RAW__
            int i = asBC_INTARG(byteCode);                                                                                         __RAW__
            asCScriptFunction *asfunc = ((asCScriptEngine*)m_engine)->GetScriptFunction(i);                                        __RAW__
            if (asfunc && strcmp("$fact", asfunc->GetName())                                                                       __RAW__
                && strcmp("$list", asfunc->GetName()) && strncmp("$beh", asfunc->GetName(), 4))                                    __RAW__
            {                                                                                                                      __RAW__
                func.m_output += "\3asDWORD * expected = l_bc;\\n";                                                                __RAW__
\12
                func.m_output += "\3    __PLACEHOLDER2__\\n";                                                                      __RAW__
                func.m_output += "\3if (__func->GetJITFunction() == " + GetAOTName(asfunc) + ")\\n";                               __RAW__
                func.m_output += "\3{\\n";                                                                                         __RAW__
                func.m_output += "\3    " + GetAOTName(asfunc) + "(registers, 0);\\n";                                             __RAW__
                func.m_output += "\3}\\n";                                                                                         __RAW__
                func.m_output += "\3\8\\n";                                                                                        __RAW__
                func.m_output += "\3\9\\n";                                                                                        __RAW__
                func.m_output += "\3\10\\n";                                                                                       __RAW__
                func.m_output += "\3if (l_bc != expected)\\n";                                                                     __RAW__
                func.m_output += "\3    __PLACEHOLDER2__\\n";                                                                      __RAW__
            }                                                                                                                      __RAW__
            else                                                                                                                   __RAW__
#endif                                                                                                                             __RAW__
            {                                                                                                                      __RAW__
                func.m_output += "\3__PLACEHOLDER2__\\n";                                                                          __RAW__
            }                                                                                                                      __RAW__
\3""" % (bytecode[0] == "asBC_CALL" or bytecode[0] == "asBC_ALLOC"), data)

    # FIXME: my_callfunc.h requires more work, still contains old version logic
    # if bytecode[0] == "asBC_CALLSYS":
    #     match = callsystemre2.search(data)
    #     if not match:
    #         raise Exception("CallSystemFunction pattern not found for %s" % bytecode[0])
    #     idx = match.group(1)
    #     object_pointer = "0"  # FIXME: new version doesn't have this param'
    #     if not re.search(r"asBC_\w+ARG", idx):
    #         m2 = re.search(r"%s\s*=\s*(asBC_\w+ARG.*?);" % idx, data);
    #         if not m2:
    #             raise Exception("asBC_*ARG not found... %s\n%s" % (idx, data))
    #         idx = m2.group(1)
    #     idx = idx.replace("l_bc", "byteCode")
    #
    #     data = "{\nvoid *objectPointer = %s;\n%s}\n" % (object_pointer, data)
    #     data = callsystemre2.sub("""
    #         char __tmp[128];                                         __RAW__
    #         snprintf(__tmp, 128, "callsys_%%d_end", callsyscount++); __RAW__
    #         std::string UNIQUE_CALLSYS_END_LABEL(__tmp);             __RAW__
    #         #define __id %s                                          __RAW__
    #         #define goto_label %s_end                                __RAW__
    #         #include "my_callfunc.h"                                 __RAW__
    #         #undef goto_label                                        __RAW__
    #         #undef __id                                              __RAW__
    #         """ % (idx, bytecode[0]), data)

    if bytecode[0] == "asBC_RET":
        data = retre.sub(r"""\1\2
\1registers->stackPointer += \3;
            func.m_output += "\1__PLACEHOLDER2__\\n"; __RAW__""", data)

    lines = data.split("\n")
    for line in lines:
        if "break;" in line:
            line = line.replace("break;", "")


        line = line.replace("this", "context")
        line = line.replace("CallSc", "context->CallSc")
        line = line.replace("CallInt", "context->CallInt")
        line = line.replace("CallLine", "context->CallLine")
        line = line.replace("SetInternal", "context->SetInternal")
        line = line.replace("PopCallState", "context->PopCallState")
        line = line.replace("m_regs.", "registers->")

        if "__PLACEHOLDER2__" in line:
            line = line.replace("__PLACEHOLDER2__", "goto \" + func.m_name + \"_end2;")

        if "__RAW__" in line:
            line = line.replace("__RAW__", "")
            emit(line)
            continue

        line = line.replace("%", "%%")

        if "return" in line:
            line =  """            func.m_output += "%sgoto " + func.m_name + "_end;\\n";""" % line.replace("return;", "")
            emit(line)
            continue

        line = line.replace("m_", "context->m_")


        if commentre.match(line) or len(line.strip()) == 0:
            continue

        jump = jumpre.match(line)

        count = 0
        for m in argre.finditer(line):
            if "PTR" in m.group(1):
                continue
            if count == 0:
                emit("            {")
            emit("                %s aottmp%d = %s(byteCode%s);" % (gettypename(m.group(1)), count, m.group(1), m.group(2)))
            line = line.replace(m.string[m.start(1):m.end(2)+1], gettypeprintf(m.group(1)))
            count += 1

        if jump:
            emit("            {")
            emit("                unsigned long target = asBC_INTARG(byteCode)+2 + offset;")
            emit("                func.m_output += \"                {\\n\";")
        if count == 0:
            emit("            func.m_output += \"%s\\n\";" % line)
        else:
            emit("                char aotbuf[BUFSIZE];")
            emit("                snprintf(aotbuf, BUFSIZE, \"%s\\n\", %s);" % (line, ",".join(["aottmp%d" % d for d in range(count)])))
            emit("                func.m_output += aotbuf;")
        if jump:
            emit("                char aotbuf2[BUFSIZE];")
            emit("                snprintf(aotbuf2, BUFSIZE, \"                    goto bytecodeoffset_%lu;\\n\", target);")
            emit("                func.m_output += aotbuf2;")
            emit("                func.m_output += \"                }\\n\";")
            emit("            }")
        if count != 0:
            emit("            }")

    emit("            break;")
    emit("        }")

emit("        default:")
emit("            ASSERT(\"can't handle that opcode...\");")
emit("            break;")
emit("    }")
emit("}")

if out is not sys.stdout:
    out.close()
