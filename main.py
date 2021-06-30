from ctypes import (
    CFUNCTYPE, POINTER, CDLL, c_char_p, c_int, c_uint, c_void_p, c_double,
    Structure, pointer, cast, py_object, addressof, byref
)
import random
import sys
from copy import deepcopy

to_handle = py_object

kOfxStatOK = 0
kOfxStatFailed = 1
kOfxStatErrFatal = 2
kOfxStatErrUnknown = 3
kOfxStatErrMissingHostFeature = 4
kOfxStatErrUnsupported = 5
kOfxStatErrExists = 6
kOfxStatErrFormat = 7
kOfxStatErrMemory = 8
kOfxStatErrBadHandle = 9
kOfxStatErrBadIndex = 10
kOfxStatErrValue = 11
kOfxStatReplyYes = 12
kOfxStatReplyNo = 13
kOfxStatReplyDefault = 14

kOfxMeshAttribPoint = b"OfxMeshAttribPoint"
kOfxMeshAttribCorner = b"OfxMeshAttribCorner"
kOfxMeshAttribFace = b"OfxMeshAttribFace"
kOfxMeshAttribMesh = b"OfxMeshAttribMesh"

kOfxMeshAttribPointPosition = b"OfxMeshAttribPointPosition"
kOfxMeshAttribCornerPoint = b"OfxMeshAttribCornerPoint"
kOfxMeshAttribFaceSize = b"OfxMeshAttribFaceSize"

kOfxMeshAttribTypeUByte = b"OfxMeshAttribTypeUByte"
kOfxMeshAttribTypeInt = b"OfxMeshAttribTypeInt"
kOfxMeshAttribTypeFloat = b"OfxMeshAttribTypeFloat"

OfxStatus = c_int
OfxTime = c_double
OfxPropertySet = dict
OfxPropertySetHandle = POINTER(py_object)

OfxParamSet = dict
OfxParamSetHandle = POINTER(py_object)

OfxInputSet = dict
OfxInputSetHandle = POINTER(py_object)

class OfxAttribute:
    def __init__(self, name, attachment, component_count, attribute_type):
        self.name = name
        self.attachment = attachment
        self.component_count = component_count
        self.attribute_type = attribute_type
        self.properties = OfxPropertySet()

class OfxMesh:
    def __init__(self):
        self.properties = OfxPropertySet()
        self.attributes = {
            kOfxMeshAttribPoint: {
                kOfxMeshAttribPointPosition: OfxAttribute(kOfxMeshAttribPointPosition, kOfxMeshAttribPoint, 3, kOfxMeshAttribTypeFloat)
            }
        }

OfxMeshHandle = POINTER(py_object)

class OfxMeshInput:
    def __init__(self, name):
        self.name = name
        self.properties = OfxPropertySet()
        self.mesh = OfxMesh()

OfxMeshInputHandle = POINTER(py_object)

class OfxMeshEffect:
    def __init__(self):
        self.params = OfxParamSet()
        self.inputs = OfxInputSet()

OfxMeshEffectHandle = POINTER(py_object)

class OfxHost(Structure):
    _fields_ = [
        ("host", OfxPropertySetHandle),
        ("fetchSuite", CFUNCTYPE(c_void_p, OfxPropertySetHandle, c_char_p, c_int)),
    ]

    def __init__(self):
        self.fetchSuite = self._fetchSuite

        self.host_props = OfxPropertySet()
        self.host_props['host_instance'] = self
        self.host = pointer(to_handle(self.host_props))

        self.suites = {
            b'OfxPropertySuite': { 1: OfxPropertySuiteV1() },
            b'OfxParameterSuite': { 1: OfxParameterSuiteV1() },
            b'OfxMeshEffectSuite': { 1: OfxMeshEffectSuiteV1() },
            b'OfxMessageSuite': { 2: OfxMessageSuiteV2() },
        }

    @staticmethod
    @CFUNCTYPE(c_void_p, OfxPropertySetHandle, c_char_p, c_int)
    def _fetchSuite(host_props_p, suite_name, suite_version):
        host_props = host_props_p.contents.value
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
        ("propSetPointer",   CFUNCTYPE(OfxStatus, OfxPropertySetHandle, c_char_p, c_int, c_void_p)),
        ("propSetString",    CFUNCTYPE(OfxStatus, OfxPropertySetHandle, c_char_p, c_int, c_char_p)),
        ("propSetDouble",    CFUNCTYPE(OfxStatus, OfxPropertySetHandle, c_char_p, c_int, c_double)),
        ("propSetInt",       CFUNCTYPE(OfxStatus, OfxPropertySetHandle, c_char_p, c_int, c_int)),
        ("propSetPointerN",  CFUNCTYPE(OfxStatus, OfxPropertySetHandle, c_char_p, c_int, POINTER(c_void_p))),
        ("propSetStringN",   CFUNCTYPE(OfxStatus, OfxPropertySetHandle, c_char_p, c_int, POINTER(c_char_p))),
        ("propSetDoubleN",   CFUNCTYPE(OfxStatus, OfxPropertySetHandle, c_char_p, c_int, POINTER(c_double))),
        ("propSetIntN",      CFUNCTYPE(OfxStatus, OfxPropertySetHandle, c_char_p, c_int, POINTER(c_int))),
        ("propGetPointer",   CFUNCTYPE(OfxStatus, OfxPropertySetHandle, c_char_p, c_int, POINTER(c_void_p))),
        ("propGetString",    CFUNCTYPE(OfxStatus, OfxPropertySetHandle, c_char_p, c_int, POINTER(c_char_p))),
        ("propGetDouble",    CFUNCTYPE(OfxStatus, OfxPropertySetHandle, c_char_p, c_int, POINTER(c_double))),
        ("propGetInt",       CFUNCTYPE(OfxStatus, OfxPropertySetHandle, c_char_p, c_int, POINTER(c_int))),
        ("propGetPointerN",  CFUNCTYPE(OfxStatus, OfxPropertySetHandle, c_char_p, c_int, POINTER(c_void_p))),
        ("propGetStringN",   CFUNCTYPE(OfxStatus, OfxPropertySetHandle, c_char_p, c_int, POINTER(c_char_p))),
        ("propGetDoubleN",   CFUNCTYPE(OfxStatus, OfxPropertySetHandle, c_char_p, c_int, POINTER(c_double))),
        ("propGetIntN",      CFUNCTYPE(OfxStatus, OfxPropertySetHandle, c_char_p, c_int, POINTER(c_int))),
        ("propReset",        CFUNCTYPE(OfxStatus, OfxPropertySetHandle, c_char_p)),
        ("propGetDimension", CFUNCTYPE(OfxStatus, OfxPropertySetHandle, c_char_p, POINTER(c_int))),
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

    @staticmethod
    def _propGetInt(property_set_p, name, component, value_p):
        exit(1)

class OfxParameterSuiteV1(Structure, OfxSuite):
    _fields_ = [
        ("paramDefine",            CFUNCTYPE(OfxStatus, OfxParamSetHandle, c_char_p, c_char_p, POINTER(OfxPropertySetHandle))),
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
    def _paramDefine(param_set_p, param_type, name, property_set_pp):
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
        if property_set_pp:
            property_set_pp.contents.contents = to_handle(param_set[name]["properties"])
        return kOfxStatOK

class OfxMeshEffectSuiteV1(Structure, OfxSuite):
    _fields_ = [
        ("getPropertySet",        CFUNCTYPE(OfxStatus, c_int)),
        ("getParamSet",           CFUNCTYPE(OfxStatus, OfxMeshEffectHandle, POINTER(OfxParamSetHandle))),
        ("inputDefine",           CFUNCTYPE(OfxStatus, OfxMeshEffectHandle, c_char_p, POINTER(OfxMeshInputHandle), POINTER(OfxPropertySetHandle))),
        ("inputGetHandle",        CFUNCTYPE(OfxStatus, OfxMeshEffectHandle, c_char_p, POINTER(OfxMeshInputHandle), POINTER(OfxPropertySetHandle))),
        ("inputGetPropertySet",   CFUNCTYPE(OfxStatus, c_int)),
        ("inputRequestAttribute", CFUNCTYPE(OfxStatus, c_int)),
        ("inputGetMesh",          CFUNCTYPE(OfxStatus, OfxMeshInputHandle, OfxTime, POINTER(OfxMeshHandle), POINTER(OfxPropertySetHandle))),
        ("inputReleaseMesh",      CFUNCTYPE(OfxStatus, c_int)),
        ("attributeDefine",       CFUNCTYPE(OfxStatus, c_int)),
        ("meshGetAttribute",      CFUNCTYPE(OfxStatus, OfxMeshHandle, c_char_p, c_char_p, POINTER(OfxPropertySetHandle))),
        ("meshGetPropertySet",    CFUNCTYPE(OfxStatus, c_int)),
        ("meshAlloc",             CFUNCTYPE(OfxStatus, c_int)),
        ("abort",                 CFUNCTYPE(OfxStatus, c_int)),
    ]

    def __init__(self):
        self.initFunctionPointers()

    @staticmethod
    def _getParamSet(mesh_effect_p, param_set_pp):
        mesh_effect = mesh_effect_p.contents.value
        print(f"Getting parameter set from mesh {mesh_effect}")
        cast(param_set_pp, c_void_p)  # for some reason this line is required
        param_set_pp.contents.contents = to_handle(mesh_effect.params)
        return kOfxStatOK

    @staticmethod
    def _inputDefine(mesh_effect_p, name, input_pp, input_props_pp):
        print(f"Defining input '{name.decode()}'")
        mesh_effect = mesh_effect_p.contents.value

        mesh_input = OfxMeshInput(name)
        mesh_effect.inputs[name] = mesh_input

        cast(input_pp, c_void_p)  # for some reason this line is required
        input_pp.contents.contents = to_handle(mesh_input)

        if input_props_pp:
            cast(input_props_pp, c_void_p)  # for some reason this line is required
            input_props_pp.contents.contents = to_handle(mesh_input.properties)

        return kOfxStatOK

    @staticmethod
    def _inputGetHandle(mesh_effect_p, name, input_pp, input_props_pp):
        print(f"Getting input '{name.decode()}'")
        mesh_effect = mesh_effect_p.contents.value

        if name not in mesh_effect.inputs:
            print(f"Input does not exist: '{name.decode()}'")
            return kOfxStatErrBadIndex

        mesh_input = mesh_effect.inputs[name]

        cast(input_pp, c_void_p)  # for some reason this line is required
        input_pp.contents.contents = to_handle(mesh_input)

        if input_props_pp:
            cast(input_props_pp, c_void_p)  # for some reason this line is required
            input_props_pp.contents.contents = to_handle(mesh_input.properties)

        return kOfxStatOK

    @staticmethod
    def _inputGetMesh(mesh_input_p, time, mesh_pp, mesh_props_pp):
        print(f"Getting input mesh at time {time}")
        mesh_input = mesh_input_p.contents.value

        mesh = mesh_input.mesh

        cast(mesh_pp, c_void_p)  # for some reason this line is required
        mesh_pp.contents.contents = to_handle(mesh)

        if mesh_props_pp:
            cast(mesh_props_pp, c_void_p)  # for some reason this line is required
            mesh_props_pp.contents.contents = to_handle(mesh.properties)

        return kOfxStatOK

    @staticmethod
    def _meshGetAttribute(mesh_p, attachment, name, attribute_pp):
        print(f"Getting {attachment.decode()} attribute '{name.decode()}'")
        mesh = mesh_p.contents.value
        attribute = mesh.attributes.get(attachment, {}).get(name)
        if attribute is None:
            print(f"Attribute does not exist: {attachment.decode()}/{name.decode()}")
            return kOfxStatErrBadIndex

        cast(attribute_pp, c_void_p)  # for some reason this line is required
        attribute_pp.contents.contents = to_handle(attribute)
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
    descriptor_handle = to_handle(descriptor)
    status = plugin.mainEntry(kOfxActionDescribe, byref(descriptor_handle), None, None)
    print(f"kOfxActionDescribe status = {status}")

    instance = deepcopy(descriptor)
    instance_handle = to_handle(instance)
    status = plugin.mainEntry(kOfxActionCreateInstance, byref(instance_handle), None, None)
    print(f"kOfxActionCreateInstance status = {status}")

    status = plugin.mainEntry(kOfxMeshEffectActionCook, byref(instance_handle), None, None)
    print(f"kOfxActionCook status = {status}")

#main(r"E:\SourceCode\MfxCascade\build\MfxCascade.ofx.bundle\Win64\MfxCascade.ofx")
main(r"E:\SourceCode\MfxExamples\build\Release\mfx_examples.ofx")
