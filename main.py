from ctypes import (
    CFUNCTYPE, POINTER, CDLL, c_char_p, c_int, c_uint, c_void_p, c_double,
    Structure, pointer, cast, py_object, addressof, byref
)
import random
import sys
from copy import deepcopy

kOfxStatOK = 0
kOfxStatErrBadHandle = 9

OfxStatus = c_int
OfxPropertySet = dict
OfxPropertySetHandle = py_object

OfxParamSet = dict
OfxParamSetHandle = py_object

OfxInputSet = dict
OfxInputSetHandle = py_object

class OfxMeshInput:
    def __init__(self, name):
        self.name = name
        self.properties = OfxPropertySet()

OfxMeshInputHandle = py_object

class OfxMeshEffect:
    def __init__(self):
        self.params = OfxParamSet()
        self.params['foo'] = "bar"

        self.inputs = OfxInputSet()

OfxMeshEffectHandle = py_object

class OfxHost(Structure):
    _fields_ = [
        ("host", OfxPropertySetHandle),
        ("fetchSuite", CFUNCTYPE(c_void_p, OfxPropertySetHandle, c_char_p, c_int)),
    ]

    def __init__(self):
        self.fetchSuite = self._fetchSuite

        self.host_props = OfxPropertySet()
        self.host_props['host_instance'] = self
        self.host = py_object(self.host_props)

        self.suites = {
            b'OfxPropertySuite': { 1: OfxPropertySuiteV1() },
            b'OfxParameterSuite': { 1: OfxParameterSuiteV1() },
            b'OfxMeshEffectSuite': { 1: OfxMeshEffectSuiteV1() },
            b'OfxMessageSuite': { 2: OfxMessageSuiteV2() },
        }

    @staticmethod
    @CFUNCTYPE(c_void_p, OfxPropertySetHandle, c_char_p, c_int)
    def _fetchSuite(host_props, suite_name, suite_version):
        self = host_props['host_instance']
        print(f"Fetching suite {suite_name}, version {suite_version}")
        if suite_name in self.suites:
            if suite_version in self.suites[suite_name]:
                suite = self.suites[suite_name][suite_version]
                return cast(pointer(suite), c_void_p).value
            else:
                print(f"Warning: Suite version not found: {suite_version} (suite '{suite_name.decode()}')")
        else:
            print(f"Warning: Suite not found: '{suite_name.decode()}'")
        return None


class OfxPlugin(Structure):
    _fields_ = [
        ("pluginApi", c_char_p),
        ("apiVersion", c_int),
        ("pluginIdentifier", c_char_p),
        ("pluginVersionMajor", c_uint),
        ("pluginVersionMinor", c_uint),
        ("setHost", CFUNCTYPE(None, POINTER(OfxHost))),
        ("mainEntry", CFUNCTYPE(OfxStatus, c_char_p, c_void_p, OfxPropertySetHandle, OfxPropertySetHandle)),
    ]

class OfxSuite:
    def initFunctionPointers(self):
        for attr, ctype in self._fields_:
            if hasattr(self, "_" + attr):
                f = getattr(self, "_" + attr)
                setattr(self, attr, ctype(f))
            else:
                setattr(self, attr, ctype(self.makeMockMethod(attr)))

    @classmethod
    def makeMockMethod(cls, attr):
        def f(*args):
            print(f"Call mock {cls.__name__}::{attr}")
            return kOfxStatOK
        return f

class OfxPropertySuiteV1(Structure, OfxSuite):
    _fields_ = [
        ("propSetPointer",   CFUNCTYPE(OfxStatus, POINTER(OfxPropertySetHandle), c_char_p, c_int, c_void_p)),
        ("propSetString",    CFUNCTYPE(OfxStatus, POINTER(OfxPropertySetHandle), c_char_p, c_int, c_char_p)),
        ("propSetDouble",    CFUNCTYPE(OfxStatus, POINTER(OfxPropertySetHandle), c_char_p, c_int, c_double)),
        ("propSetInt",       CFUNCTYPE(OfxStatus, POINTER(OfxPropertySetHandle), c_char_p, c_int, c_int)),
        ("propSetPointerN",  CFUNCTYPE(OfxStatus, POINTER(OfxPropertySetHandle), c_char_p, c_int, POINTER(c_void_p))),
        ("propSetStringN",   CFUNCTYPE(OfxStatus, POINTER(OfxPropertySetHandle), c_char_p, c_int, POINTER(c_char_p))),
        ("propSetDoubleN",   CFUNCTYPE(OfxStatus, POINTER(OfxPropertySetHandle), c_char_p, c_int, POINTER(c_double))),
        ("propSetIntN",      CFUNCTYPE(OfxStatus, POINTER(OfxPropertySetHandle), c_char_p, c_int, POINTER(c_int))),
        ("propGetPointer",   CFUNCTYPE(OfxStatus, POINTER(OfxPropertySetHandle), c_char_p, c_int, POINTER(c_void_p))),
        ("propGetString",    CFUNCTYPE(OfxStatus, POINTER(OfxPropertySetHandle), c_char_p, c_int, POINTER(c_char_p))),
        ("propGetDouble",    CFUNCTYPE(OfxStatus, POINTER(OfxPropertySetHandle), c_char_p, c_int, POINTER(c_double))),
        ("propGetInt",       CFUNCTYPE(OfxStatus, POINTER(OfxPropertySetHandle), c_char_p, c_int, POINTER(c_int))),
        ("propGetPointerN",  CFUNCTYPE(OfxStatus, POINTER(OfxPropertySetHandle), c_char_p, c_int, POINTER(c_void_p))),
        ("propGetStringN",   CFUNCTYPE(OfxStatus, POINTER(OfxPropertySetHandle), c_char_p, c_int, POINTER(c_char_p))),
        ("propGetDoubleN",   CFUNCTYPE(OfxStatus, POINTER(OfxPropertySetHandle), c_char_p, c_int, POINTER(c_double))),
        ("propGetIntN",      CFUNCTYPE(OfxStatus, POINTER(OfxPropertySetHandle), c_char_p, c_int, POINTER(c_int))),
        ("propReset",        CFUNCTYPE(OfxStatus, POINTER(OfxPropertySetHandle), c_char_p)),
        ("propGetDimension", CFUNCTYPE(OfxStatus, POINTER(OfxPropertySetHandle), c_char_p, POINTER(c_int))),
    ]

    def __init__(self):
        self.initFunctionPointers()

    @staticmethod
    def _propSetDouble(property_set_p, name, component, value):
        property_set = property_set_p.contents.value
        print(f"Setting property {name.decode()}[{component}] to {value}")
        if name not in property_set:
            property_set[name] = [None, None, None, None]
        property_set[name][component] = value
        return kOfxStatOK

    _propSetString = _propSetDouble
    _propSetInt = _propSetDouble

class OfxParameterSuiteV1(Structure, OfxSuite):
    _fields_ = [
        ("paramDefine",            CFUNCTYPE(OfxStatus, POINTER(OfxParamSetHandle), c_char_p, c_char_p, POINTER(POINTER(OfxPropertySetHandle)))),
        ("paramGetHandle",         CFUNCTYPE(OfxStatus, c_int)),
        ("paramSetGetPropertySet", CFUNCTYPE(OfxStatus, c_int)),
        ("paramGetPropertySet",    CFUNCTYPE(OfxStatus, c_int)),
        ("paramGetValue",          CFUNCTYPE(OfxStatus, c_int)),
        ("paramGetValueAtTime",    CFUNCTYPE(OfxStatus, c_int)),
        ("paramGetDerivative",     CFUNCTYPE(OfxStatus, c_int)),
        ("paramGetIntegral",       CFUNCTYPE(OfxStatus, c_int)),
        ("paramSetValue",          CFUNCTYPE(OfxStatus, c_int)),
        ("paramSetValueAtTime",    CFUNCTYPE(OfxStatus, c_int)),
        ("paramGetNumKeys",        CFUNCTYPE(OfxStatus, c_int)),
        ("paramGetKeyTime",        CFUNCTYPE(OfxStatus, c_int)),
        ("paramGetKeyIndex",       CFUNCTYPE(OfxStatus, c_int)),
        ("paramDeleteKey",         CFUNCTYPE(OfxStatus, c_int)),
        ("paramDeleteAllKeys",     CFUNCTYPE(OfxStatus, c_int)),
        ("paramCopy",              CFUNCTYPE(OfxStatus, c_int)),
        ("paramEditBegin",         CFUNCTYPE(OfxStatus, c_int)),
        ("paramEditEnd",           CFUNCTYPE(OfxStatus, c_int)),
    ]

    def __init__(self):
        self.initFunctionPointers()

    @staticmethod
    def _paramDefine(param_set_p, param_type, name, property_set_p):
        print(f"Defining parameter '{name.decode()}'")
        if not param_set_p:
            print("Invalid parameter set!")
            return kOfxStatErrBadHandle
        param_set = param_set_p.contents.value
        param_set[name] = {
            "name": name,
            "type": param_type,
            "properties": OfxPropertySet(),
        }
        if property_set_p.contents:
            property_set_p.contents.contents = OfxPropertySetHandle(param_set[name]["properties"])
        return kOfxStatOK

class OfxMeshEffectSuiteV1(Structure, OfxSuite):
    _fields_ = [
        ("getPropertySet",        CFUNCTYPE(OfxStatus, c_int)),
        ("getParamSet",           CFUNCTYPE(OfxStatus, POINTER(OfxMeshEffectHandle), POINTER(POINTER(OfxParamSetHandle)))),
        ("inputDefine",           CFUNCTYPE(OfxStatus, POINTER(OfxMeshEffectHandle), c_char_p, POINTER(POINTER(OfxMeshInputHandle)), POINTER(POINTER(OfxPropertySetHandle)))),
        ("inputGetHandle",        CFUNCTYPE(OfxStatus, c_int)),
        ("inputGetPropertySet",   CFUNCTYPE(OfxStatus, c_int)),
        ("inputRequestAttribute", CFUNCTYPE(OfxStatus, c_int)),
        ("inputGetMesh",          CFUNCTYPE(OfxStatus, c_int)),
        ("inputReleaseMesh",      CFUNCTYPE(OfxStatus, c_int)),
        ("attributeDefine",       CFUNCTYPE(OfxStatus, c_int)),
        ("meshGetAttribute",      CFUNCTYPE(OfxStatus, c_int)),
        ("meshGetPropertySet",    CFUNCTYPE(OfxStatus, c_int)),
        ("meshAlloc",             CFUNCTYPE(OfxStatus, c_int)),
        ("abort",                 CFUNCTYPE(OfxStatus, c_int)),
    ]

    def __init__(self):
        self.initFunctionPointers()

    @staticmethod
    def _getParamSet(mesh_effect_p, param_set_h):
        mesh_effect = mesh_effect_p.contents.value
        print(f"Getting parameter set from mesh {mesh_effect}")
        print(mesh_effect.params)
        cast(param_set_h, c_void_p)  # for some reason this line is required
        param_set_h.contents.contents = OfxParamSetHandle(mesh_effect.params)
        return kOfxStatOK

    @staticmethod
    def _inputDefine(mesh_effect_p, name, input_p, input_props_p):
        print(f"Defining input '{name.decode()}'")
        mesh_effect = mesh_effect_p.contents.value

        mesh_input = OfxMeshInput(name)
        mesh_effect.inputs[name] = mesh_input

        input_p.contents.contents = OfxMeshInputHandle(mesh_input)

        if input_props_p.contents:
            input_props_p.contents.contents = OfxPropertySetHandle(mesh_input.properties)

        return kOfxStatOK

class OfxMessageSuiteV2(Structure, OfxSuite):
    _fields_ = [
        ("message",                CFUNCTYPE(OfxStatus, c_int)),
        ("setPersistentMessage",   CFUNCTYPE(OfxStatus, c_int)),
        ("clearPersistentMessage", CFUNCTYPE(OfxStatus, c_int)),
    ]

    def __init__(self):
        self.initFunctionPointers()

kOfxActionLoad = b"OfxActionLoad"
kOfxActionDescribe = b"OfxActionDescribe"
kOfxActionCreateInstance = b"OfxActionCreateInstance"
kOfxMeshEffectActionCook = b"OfxMeshEffectActionCook"

def main(dll_filename):
    hllDll = CDLL(dll_filename)
    hllApiProto = CFUNCTYPE(c_int)
    hllApiParams = ()
    OfxGetNumberOfPlugins = hllApiProto(("OfxGetNumberOfPlugins", hllDll), hllApiParams)
    n = OfxGetNumberOfPlugins()
    print(f"Found {n} plugins")

    hllApiProto = CFUNCTYPE(POINTER(OfxPlugin), c_int)
    hllApiParams = ((1, "nth", 0),)
    OfxGetPlugin = hllApiProto(("OfxGetPlugin", hllDll), hllApiParams)
    nth = c_int(0)
    plugin = OfxGetPlugin(nth).contents
    print(f"Plugin #0 is called '{plugin.pluginIdentifier.decode()}'")

    host = OfxHost()
    plugin.setHost(host)

    status = plugin.mainEntry(kOfxActionLoad, None, None, None)

    descriptor = OfxMeshEffect()
    descriptor_handle = OfxMeshEffectHandle(descriptor)
    status = plugin.mainEntry(kOfxActionDescribe, byref(descriptor_handle), None, None)
    print(f"kOfxActionDescribe status = {status}")

    instance = deepcopy(descriptor)
    instance_handle = OfxMeshEffectHandle(instance)
    status = plugin.mainEntry(kOfxActionCreateInstance, byref(instance_handle), None, None)
    print(f"kOfxActionCreateInstance status = {status}")

    status = plugin.mainEntry(kOfxMeshEffectActionCook, byref(instance_handle), None, None)
    print(f"kOfxActionCook status = {status}")

#main(r"E:\SourceCode\MfxCascade\build\MfxCascade.ofx.bundle\Win64\MfxCascade.ofx")
main(r"E:\SourceCode\MfxExamples\build\Release\mfx_examples.ofx")
