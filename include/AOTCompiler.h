/*
 * Copyright (c) 2012 Fredrik Ehnbom
 *
 * This software is provided 'as-is', without any express or implied
 * warranty. In no event will the authors be held liable for any damages
 * arising from the use of this software.
 *
 * Permission is granted to anyone to use this software for any purpose,
 * including commercial applications, and to alter it and redistribute it
 * freely, subject to the following restrictions:
 *
 *    1. The origin of this software must not be misrepresented; you must not
 *    claim that you wrote the original software. If you use this software
 *    in a product, an acknowledgment in the product documentation would be
 *    appreciated but is not required.
 *
 *    2. Altered source versions must be plainly marked as such, and must not be
 *    misrepresented as being the original software.
 *
 *    3. This notice may not be removed or altered from any source
 *    distribution.
 */
#ifndef __INCLUDED_AOTCOMPILER_H
#define __INCLUDED_AOTCOMPILER_H

#include <angelscript.h>
#include <as_datatype.h>
#include <map>
#include <vector>
#include "AOTFunction.h"
#include "AOTLinker.h"
#include "aot_config.h"

class AOTCompiler : public asIJITCompiler
{
public:
    struct DirectCallBinding
    {
        std::string cppDeclaration;
        std::string cppSymbol;
        std::vector<std::string> cppParamTypes;
    };

    AOTCompiler(AOTLinker *linker);
    virtual ~AOTCompiler();
    virtual int CompileFunction(asIScriptFunction *function, asJITFunction *output);
    virtual void ReleaseJITFunction(asJITFunction func);

    void SaveCode(asIBinaryStream *stream);
    void RegisterDirectCall(asIScriptFunction *function,
                            const char *cppDeclaration,
                            const char *cppSymbol,
                            const std::vector<std::string> &cppParamTypes);
private:
    std::string GetAOTName(asIScriptFunction *func);
    const DirectCallBinding *FindDirectCall(int functionId) const;
    static std::string StripTopLevelReference(const std::string &typeName);
    static std::string BuildDirectCallArgument(const asCDataType &dataType, const std::string &cppType, int stackOffset);
    asIScriptEngine *m_engine;
    AOTLinker *m_linker;
    void ProcessByteCode(asDWORD *byteCode, asUINT offset, asEBCInstr op, AOTFunction &f);
    std::vector<AOTFunction> m_functions;
    std::map<int, DirectCallBinding> m_directCalls;
};

#endif
