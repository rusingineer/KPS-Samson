#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division, absolute_import, print_function, unicode_literals
import codecs
import six
import sys
from xml.dom.minidom import parse
#from collections import OrderedDict

# имя файла для анализа
DOXYGEN_GENERATED_FILE = 'xml/classclassic__interface.xml'

# функции, которые мы пропускаем
FUNC_BLACK_LIST = ['classic_interface',           # конструктор не нужен, это в большой степени особый случай
                   '~classic_interface',          # деструктор тоже не нужен
                   'setPropertyChangedCallback',  # это я пока не хочу думать, но можно обработать наособицу
                   'setPropertyTouchedCallback',  # idem
                   'setLogCallback',              # idem
                   'FNCheckItemBarcode2',         # не представлено в .so для интерфейса в стиле C
                   'FNAcceptMakringCode',         # не представлено в .so для интерфейса в стиле C
                   'Get_TLVDataHex',              # не представлено в .so для интерфейса в стиле C
                   'Set_TLVDataHex',              # не представлено в .so для интерфейса в стиле C
                  ]

# шаблон функции по умолчанию
DEFAULT_TPL = [ 'def {fn}({fargs}):{fcomment}',
                '    return {wrapper}({args})'
              ]

DESCR_FUNC_TYPE  = { 'bool'                   : { 'ctype': 'ctypes.c_bool' },
                     'double'                 : { 'ctype': 'ctypes.c_double' },
                     'int'                    : { 'ctype': 'ctypes.c_int' },
                     'void'                   : { 'ctype': 'None',
                                                  'tpl'  : [ 'def {fn}({fargs}):{fcomment}',
                                                             '    {wrapper}({args})'
                                                           ]
                                                },
                     'int64_t'                : { 'ctype': 'ctypes.c_int64' },
                     'uint32_t'               : { 'ctype': 'ctypes.c_uint32'},
                     'uint64_t'               : { 'ctype': 'ctypes.c_uint64'},
                     'std::string'            : { 'ctype': 'ctypes.c_size_t', 
                                                  'params_trailer': ( 'ctypes.c_char_p', 'ctypes.c_size_t' ),
                                                  'tpl'  : [ 'def {fn}({fargs}):{fcomment}',
                                                             '    resultLen = {wrapper}({args}, None, 0)',
                                                             '    resultBuffer = ctypes.create_string_buffer(resultLen+1)',
                                                             '    {wrapper}({args}, resultBuffer, resultLen+1)',
                                                             '    return ctypes.string_at(resultBuffer, resultLen).decode(\'utf-8\')'
                                                           ]
                                                },
                     'std::vector< uint8_t >' : { 'ctype': 'ctypes.c_size_t', 'params_trailer': ( 'ctypes.c_char_p', 'ctypes.c_size_t' ),
                                                  'tpl'  : [ 'def {fn}({fargs}):{fcomment}',
                                                             '    resultLen = {wrapper}({args}, None, 0)',
                                                             '    resultBuffer = ctypes.create_string_buffer(resultLen+1)',
                                                             '    {wrapper}({args}, resultBuffer, resultLen+1)',
                                                             '    return ctypes.string_at(resultBuffer, resultLen)'
                                                           ]
                                                },
                     'std::time_t' :            { 'ctype': 'time_t', # https://stackoverflow.com/questions/6418221/getting-type-size-of-time-t-using-ctypes
                                                  'tpl'  : [ 'def {fn}({fargs}):{fcomment}',
                                                             '    return unwrapDateTime({wrapper}({args}))'
                                                           ]

                                                },
                     '<enum>'      :            { 'ctype': 'ctypes.c_int' },
                   }

DESCR_PARAM_TYPE = { 'bool'                           : { 'ctype': 'ctypes.c_bool' },
                     'double'                         : { 'ctype': 'ctypes.c_double' },
                     'int'                            : { 'ctype': 'ctypes.c_int' },
                     'int64_t'                        : { 'ctype': 'ctypes.c_int64' },
                     'std::time_t'                    : { 'ctype': 'time_t', # https://stackoverflow.com/questions/6418221/getting-type-size-of-time-t-using-ctypes
                                                          'tba'  : 'wrapDateTime({paramName})'
                                                        },
                     'uint32_t'                       : { 'ctype': 'ctypes.c_uint32'},
                     'uint64_t'                       : { 'ctype': 'ctypes.c_uint64'},
                     'const std::string &'            : { 'ctype': ( 'ctypes.c_char_p', 'ctypes.c_size_t' ),
                                                          'tpl'  : [ '    {paramName}Buff = wrapString({paramName})',
                                                                   ],
                                                          'tba'  : '{paramName}Buff, len({paramName}Buff)',
                                                        },
                     'const std::vector< uint8_t > &' : { 'ctype': ( 'ctypes.c_char_p', 'ctypes.c_size_t' ),
                                                          'tba'  : '{paramName}, len({paramName})',
                                                        },
                     '<enum>'                         : { 'ctype': 'ctypes.c_int' },
                   }

class EnumMember:
    mapFormatToPrefix = { '' : '',
                          'b': '0b',
                          'd': '',
                          'o': '0',
                          'x': '0x'
                        }

    def __init__(self, name, value, descr, prefferedFormat):
        self.name = name
        self.value = value
        self.prefferedFormat = prefferedFormat
        self.strValue = '{prefix}{value:{type}}'.format(prefix=self.mapFormatToPrefix[prefferedFormat], value=value, type=prefferedFormat)
        self.comment = descr.replace('\n', ' ').strip() if descr else ''


class Enum:
    def __init__(self, name, descr, members):
        self.name = name
        self.comment = descr.replace('\n', ' ').strip() if descr else ''
        self.members = members


class Param:
    def __init__(self, name, type_):
        self.name  = name
        self.type_ = type_


class Func:
    def __init__(self, name, params, type_, descr):
        self.name = name
        self.params = params
        self.type_ = type_
        self.comment = descr.replace('\n', ' ').strip().rstrip('.') if descr else ''



def getTextFromXmlElement(node):
    def getText_(node, parts):
        for child in node.childNodes:
            if child.nodeType == node.TEXT_NODE:
                if child.data:
                    parts.append(child.data)
            else:
                getText_(child, parts)
    parts = []
    getText_(node, parts)
    return ''.join(parts)


def getTextFromXmlElements(node, names):
    result = { name: None for name in names }
    for child in node.childNodes:
#        if child.nodeType == child.ELEMENT_NODE and child.nodeName in result:
        if child.nodeName in result:
            text = getTextFromXmlElement(child)
            result[child.nodeName] = text
    return result


def getMembersOfEnum(node):
    result = []
    prevValue = -1
    preferredFormat = 'd'
    for child in node.childNodes:
#        if child.nodeType == child.ELEMENT_NODE and child.nodeName == 'enumvalue':
        if child.nodeName == 'enumvalue':
           props = getTextFromXmlElements(child, ('name', 'initializer', 'briefdescription'))
#           unknownValue = False
           valueAsStr = props['initializer']
           if valueAsStr:
               valueAsStr = valueAsStr.lstrip()
               if valueAsStr.startswith('='):
                   valueAsStr = valueAsStr.lstrip('=')
               valueAsStr = valueAsStr.strip()
               try:
                   value = int(valueAsStr, 0)
               except:
                   print('unknown initializer in ' + child.toxml())
                   exit(1)
               if valueAsStr.startswith(('0x', '0X')):
                   preferredFormat = 'x'
               elif valueAsStr.startswith(('0B', '0B')):
                   preferredFormat = 'b'
               elif valueAsStr.startswith('0') and valueAsStr != '0':
                   preferredFormat = 'o'
               else:
                   preferredFormat = 'd'
           else:
               value = prevValue+1
           result.append(EnumMember(props['name'], value, props['briefdescription'], preferredFormat))
           prevValue = value
    return result


def getParamsOfFunc(node):
    result = []
    for child in node.childNodes:
#        if child.nodeType == child.ELEMENT_NODE and child.nodeName == 'param':
        if child.nodeName == 'param':
            props = getTextFromXmlElements(child, ('type', 'declname'))
            result.append(Param(props['declname'], props['type']))
    return result


def extractFromDoxygenXml(fileName):
    try:
        xmlFile = open(fileName)
    except:
        print('File %s not found.'%fileName)
        print('Did you remember to run doxygen?')
        exit(1)

    dom = parse(xmlFile)
    members = dom.getElementsByTagName('memberdef')

    enums     = []
    functions = []
    for member in members:
        kind = member.getAttribute('kind')
        if kind == 'enum':
            props = getTextFromXmlElements(member, ['name', 'briefdescription'])
            members = getMembersOfEnum(member)
            enums.append( Enum(props['name'], props['briefdescription'], members))

        elif kind == 'function':
            props = getTextFromXmlElements(member, ['name', 'argsstring', 'type', 'briefdescription'])
            if props['name'] in FUNC_BLACK_LIST:
                continue
            params = getParamsOfFunc(member)
            functions.append(Func(props['name'], params, props['type'], props['briefdescription']))
    return enums, functions


def prepareEnums(enums):
    maxSepWidth = 0
    maxNameLen  = 0
    maxValueLen = 0

    for enum in enums:
        maxSepWidth = max(maxSepWidth, len(enum.name) + 4 + len(enum.comment))
        for member in enum.members:
            maxNameLen = max(maxNameLen, len(member.name))
            maxValueLen = max(maxValueLen, len(member.strValue))

    result = []
    for enum in enums:
        result.append('#'*maxSepWidth)
        result.append('# {name}: {comment}'.format(name=enum.name, comment=enum.comment))
        for member in enum.members:
            result.append('{name:<{nw}} = {value:>{vw}} # {comment}'.format(name  = member.name, nw=maxNameLen,
                                                                            value = member.strValue, vw = maxValueLen,
                                                                            comment = member.comment
                                                                           )
                         )
    return result


def unifyTypeName(typeName, enumnames):
    if typeName in enumNames:
        return '<enum>'
    else:
        return typeName


def preparePrototypesAndWrappers(funcs, enumNames):
    mapPrototypeParamsToFuncNames = {}
    mapFuncNameToPrototypeName = {}
    prototypeKeys = []
#    mapPrototypeArgsToName = {}

    prototypes = []
    wrappers = []

    for func in funcs:
        funcTypeName = unifyTypeName(func.type_, enumNames)
        returnCType = DESCR_FUNC_TYPE[funcTypeName]['ctype']
        prototypeParams = [returnCType, 'context_p']
        for param in func.params:
            paramTypeName = unifyTypeName(param.type_, enumNames)
            paramCType = DESCR_PARAM_TYPE[paramTypeName]['ctype']
            if isinstance(paramCType, (list, tuple)):
                prototypeParams.extend(paramCType)
            else:
                prototypeParams.append(paramCType)

        trailer = DESCR_FUNC_TYPE[funcTypeName].get('params_trailer')
        if isinstance(trailer, (list, tuple)):
            prototypeParams.extend(trailer)
        elif trailer:
            prototypeParams.append(trailer)

        prototypeKey = ', '.join(prototypeParams)
        # хочется иметь сходное поведение для py2 и py3
        if prototypeKey in mapPrototypeParamsToFuncNames:
            mapPrototypeParamsToFuncNames[prototypeKey].append(func.name)
        else:
            mapPrototypeParamsToFuncNames[prototypeKey] = [func.name]
            prototypeKeys.append(prototypeKey)

    for prototypeKey in prototypeKeys:
        funcNames = mapPrototypeParamsToFuncNames[prototypeKey]
        tmp = []
        for funcName in funcNames:
            if '_' in funcName:
                txtKey = funcName.split('_', 2)[1]
            else:
                txtKey = funcName
            tmp.append((len(txtKey), txtKey, funcName))
        _, _, funcName = min(tmp)
        prototypeName = funcName + '_proto'
        for funcName in funcNames:
            mapFuncNameToPrototypeName[funcName] = prototypeName
        prototypes.append( prototypeName + ' = ctypes.CFUNCTYPE(' + prototypeKey + ')')

#    for funcName, params, rawFuncTypeName, descr in funcs:
    for func in funcs:
        prototypeName = mapFuncNameToPrototypeName[func.name]
        wrappers.append( 'self.{fn} = {protoName}((\'{fn}\', lib))'.format(fn=func.name, protoName=prototypeName))
    return prototypes, wrappers


def geneneratefuncs(funcs, enumNames):
    imp = []
#    for funcName, params, rawFuncTypeName, descr in funcs:
    for func in funcs:
        funcTypeName = unifyTypeName(func.type_, enumNames)
        funcTemplate = DESCR_FUNC_TYPE[funcTypeName].get('tpl', DEFAULT_TPL)
        funcParamNames = ['self']
        evalArgsCode = []
        args = ['self.context']
        for param in func.params:
            funcParamNames.append(param.name)
            paramTypeName = unifyTypeName(param.type_, enumNames)
            tpl = DESCR_PARAM_TYPE[paramTypeName].get('tpl')
            if tpl:
                for tplRow in tpl:
                    evalArgsCode.append(tplRow.format(paramName=param.name))
            tba = DESCR_PARAM_TYPE[paramTypeName].get('tba')
            if tba:
                args.append(tba.format(paramName=param.name))
            else:
                args.append(param.name)

        code = []
        templateVars = { 'fn'       : func.name,
                         'fargs'    : ', '.join(funcParamNames),
                         'fcomment' : (' # '+func.comment) if func.comment else '',
                         'wrapper'  : 'classicInterfaceWrap.' + func.name,
                         'args'     : ', '.join(args)
                       }
        for funcTemplateRow in funcTemplate:
#            print('='*80)
#            print(funcTemplateRow)
            code.append(funcTemplateRow.format(**templateVars))
        code = code[:1]  + evalArgsCode + code[1:]
        imp.append( '\n'.join(code))
    return imp


def prepareProperties(funcs):
    maxPropNameLen = 0
    propNames = []
    propDict = {}
    for func in funcs:
        funcName = func.name
        getter = setter = None
        if funcName.startswith('Set_'):
            propName = funcName[4:]
            setter   = funcName
        elif funcName.startswith('Get_'):
            propName = funcName[4:]
            getter   = funcName
        else:
            continue
        propDef = propDict.setdefault(propName, {})
        if not propDef:
            propNames.append(propName)
        if getter:
            propDef['g']=funcName
            propDef['d']=func.comment
        if setter:
            propDef['s']=funcName
        maxPropNameLen = max(maxPropNameLen, len(propName))
    props = []
    for propName in propNames:
        propDef = propDict[propName]
        props.append('{propName:<{pw}} = property(fget={getter:<{w}}, fset={setter:<{w}}){comment}'.format( 
                      propName = propName, pw=maxPropNameLen,
                      getter   = propDef.get('g', 'None'), w = maxPropNameLen+4,
                      setter   = propDef.get('s', 'None'),
                      comment  = (' # ' + propDef.get('d') ) if propDef.get('d') else ''
                      )
                    )
    return props


def populateTemplate(templateFileName, prototypes, wrappers, enums, imps, props):
    for row in codecs.open(templateFileName, encoding='utf-8'):
        row = row.rstrip()
        if '{FUNC_TYPES}' in row:
            skip = row.split('#')[0]
            for prototype in prototypes:
                print(skip+prototype)
        elif '{FUNC_WRAPPERS}' in row:
            skip = row.split('#')[0]
            for wrapper in wrappers:
                print(skip+wrapper)
        elif '{ENUMS}' in row:
            skip = row.split('#')[0]
            for enum in enums:
                print(skip+enum)
        elif '{FUNC_IMPS}' in row:
            skip = row.split('#')[0]
            for imp in imps:
                for impRow in imp.split('\n'):
                    print(skip+impRow)
                print()
        elif '{PROPS}' in row:
            skip = row.split('#')[0]
            for prop in props:
                print(skip+prop)
        elif '{WARN}' in row:
            print('# This file is generated automatically, all changes will be lost!')
        else:
            print(row)

if six.PY2:
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout)

enums, funcs = extractFromDoxygenXml(DOXYGEN_GENERATED_FILE)
enumNames = [enum.name for enum in enums]

prototypes, wrappers = preparePrototypesAndWrappers(funcs, enumNames)
imps = geneneratefuncs(funcs, enumNames)
props = prepareProperties(funcs)
populateTemplate('template_fr_drv_ng.py', prototypes, wrappers, prepareEnums(enums), imps, props)


