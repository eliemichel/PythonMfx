from ctypes import (
    CFUNCTYPE, POINTER, CDLL, c_char_p, c_int, c_uint, c_void_p, c_double, c_float, c_bool,
    Structure, pointer, cast, py_object, addressof, byref, c_ubyte, sizeof
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

kOfxMeshAttribPropData = b"OfxMeshAttribPropData"
kOfxMeshAttribPropIsOwner = b"OfxMeshAttribPropIsOwner"
kOfxMeshAttribPropStride = b"OfxMeshAttribPropStride"
kOfxMeshAttribPropComponentCount = b"OfxMeshAttribPropComponentCount"
kOfxMeshAttribPropType = b"OfxMeshAttribPropType"
kOfxMeshAttribPropSemantic = b"OfxMeshAttribPropSemantic"

kOfxMeshMainInput = b"OfxMeshMainInput"
kOfxMeshMainOutput = b"OfxMeshMainOutput"

kOfxMeshPropPointCount = b"OfxMeshPropPointCount"
kOfxMeshPropCornerCount = b"OfxMeshPropCornerCount"
kOfxMeshPropFaceCount = b"OfxMeshPropFaceCount"

kOfxActionLoad = b"OfxActionLoad"
kOfxActionDescribe = b"OfxActionDescribe"
kOfxActionCreateInstance = b"OfxActionCreateInstance"
kOfxMeshEffectActionCook = b"OfxMeshEffectActionCook"

kOfxPropertySuite = b"OfxPropertySuite"
kOfxParameterSuite = b"OfxParameterSuite"
kOfxMeshEffectSuite = b"OfxMeshEffectSuite"
kOfxMessageSuite = b"OfxMessageSuite"

kOfxParamTypeInteger = b"OfxParamTypeInteger"
kOfxParamTypeDouble = b"OfxParamTypeDouble"
kOfxParamTypeBoolean = b"OfxParamTypeBoolean"
kOfxParamTypeChoice = b"OfxParamTypeChoice"
kOfxParamTypeRGBA = b"OfxParamTypeRGBA"
kOfxParamTypeRGB = b"OfxParamTypeRGB"
kOfxParamTypeDouble2D = b"OfxParamTypeDouble2D"
kOfxParamTypeInteger2D = b"OfxParamTypeInteger2D"
kOfxParamTypeDouble3D = b"OfxParamTypeDouble3D"
kOfxParamTypeInteger3D = b"OfxParamTypeInteger3D"
kOfxParamTypeString = b"OfxParamTypeString"
kOfxParamTypeCustom = b"OfxParamTypeCustom"
kOfxParamTypeGroup = b"OfxParamTypeGroup"
kOfxParamTypePage = b"OfxParamTypePage"
kOfxParamTypePushButton = b"OfxParamTypePushButton"

OfxStatus = c_int
OfxTime = c_double
OfxPropertySet = dict
OfxPropertySetHandle = POINTER(py_object)

OfxParamSet = dict
OfxParamSetHandle = POINTER(py_object)

OfxInputSet = dict
OfxInputSetHandle = POINTER(py_object)

class PyObjectWrapper(Structure):
    _fields_ = [
        ("internal", py_object),
    ]
    _internal_type_ = None

    def __init__(self, internal):
        assert(type(internal) == self.__class__._internal_type_)
        self.internal = py_object(internal)


class OfxParamInternal:
    def __init__(self, name, type):
        self.name = name
        self.type = type
        self.value = None
        self.properties = OfxPropertySet()

class OfxParam(PyObjectWrapper):
    _internal_type_ = OfxParamInternal

OfxParamHandle = POINTER(OfxParam)

class OfxAttribute(OfxPropertySet):
    def __init__(self, name, attachment, component_count, attribute_type):
        self.name = name
        self.attachment = attachment
        self.py_data = None  # python reference to the data buffer, to have the GC manage it

        self[kOfxMeshAttribPropData] = [None]
        self[kOfxMeshAttribPropIsOwner] = [True]
        self[kOfxMeshAttribPropStride] = [-1]
        self[kOfxMeshAttribPropComponentCount] = [component_count]
        self[kOfxMeshAttribPropType] = [attribute_type]
        self[kOfxMeshAttribPropSemantic] = [None]

    def allocate(self, item_count):
        if not self.is_owner:
            return

        if self.py_data is not None:
            raise Exception("Attribute already allocated")

        component_type = {
            kOfxMeshAttribTypeFloat: c_float,
            kOfxMeshAttribTypeInt: c_int,
            kOfxMeshAttribTypeUByte: c_ubyte,
        }[self.attribute_type]

        byte_stride = self.component_count * sizeof(component_type)

        self.stride = byte_stride
        if self.component_count > 1:
            full_type = component_type * self.component_count
        else:
            full_type = component_type
        self.py_data = (full_type * item_count)()
        self.data = cast(self.py_data, c_void_p)

    @property
    def data(self):
        return self[kOfxMeshAttribPropData][0]

    @data.setter
    def data(self, value):
        self[kOfxMeshAttribPropData] = [value]

    @property
    def is_owner(self):
        return self[kOfxMeshAttribPropIsOwner][0]

    @is_owner.setter
    def is_owner(self, value):
        self[kOfxMeshAttribPropIsOwner] = [value]

    @property
    def stride(self):
        return self[kOfxMeshAttribPropStride][0]

    @stride.setter
    def stride(self, value):
        self[kOfxMeshAttribPropStride] = [value]

    @property
    def component_count(self):
        return self[kOfxMeshAttribPropComponentCount][0]

    @component_count.setter
    def component_count(self, value):
        self[kOfxMeshAttribPropComponentCount] = [value]

    @property
    def attribute_type(self):
        return self[kOfxMeshAttribPropType][0]

    @attribute_type.setter
    def attribute_type(self, value):
        self[kOfxMeshAttribPropType] = [value]

    @property
    def semantic(self):
        return self[kOfxMeshAttribPropSemantic][0]

    @semantic.setter
    def semantic(self, value):
        self[kOfxMeshAttribPropSemantic] = [value]
    

class OfxMeshInternal:
    def __init__(self):
        self.properties = OfxPropertySet()
        self.attributes = {
            kOfxMeshAttribPoint: {
                kOfxMeshAttribPointPosition: OfxAttribute(kOfxMeshAttribPointPosition, kOfxMeshAttribPoint, 3, kOfxMeshAttribTypeFloat)
            },
            kOfxMeshAttribCorner: {
                kOfxMeshAttribCornerPoint: OfxAttribute(kOfxMeshAttribCornerPoint, kOfxMeshAttribCorner, 1, kOfxMeshAttribTypeInt)
            },
            kOfxMeshAttribFace: {
                kOfxMeshAttribFaceSize: OfxAttribute(kOfxMeshAttribFaceSize, kOfxMeshAttribFace, 1, kOfxMeshAttribTypeInt)
            }
        }
        self.point_count = 0
        self.corner_count = 0
        self.face_count = 0

    def allocate(self):
        type_to_count = {
            kOfxMeshAttribPoint: kOfxMeshPropPointCount,
            kOfxMeshAttribCorner: kOfxMeshPropCornerCount,
            kOfxMeshAttribFace: kOfxMeshPropFaceCount,
        }
        for item_type, attr_per_item in self.attributes.items():
            item_count = self.properties[type_to_count[item_type]][0]
            for attr in attr_per_item.values():
                attr.allocate(item_count)

    @property
    def point_count(self):
        return self.properties[kOfxMeshPropPointCount][0]

    @point_count.setter
    def point_count(self, value):
        self.properties[kOfxMeshPropPointCount] = [value]

    @property
    def corner_count(self):
        return self.properties[kOfxMeshPropCornerCount][0]

    @corner_count.setter
    def corner_count(self, value):
        self.properties[kOfxMeshPropCornerCount] = [value]

    @property
    def face_count(self):
        return self.properties[kOfxMeshPropFaceCount][0]

    @face_count.setter
    def face_count(self, value):
        self.properties[kOfxMeshPropFaceCount] = [value]
        

class OfxMesh(PyObjectWrapper):
    _internal_type_ = OfxMeshInternal

OfxMeshHandle = POINTER(OfxMesh)

class OfxMeshInputInternal:
    def __init__(self, name):
        self.name = name
        self.properties = OfxPropertySet()
        self.mesh = OfxMeshInternal()

class OfxMeshInput(PyObjectWrapper):
    _internal_type_ = OfxMeshInputInternal

OfxMeshInputHandle = POINTER(OfxMeshInput)

class OfxMeshEffectInternal:
    def __init__(self):
        self.params = OfxParamSet()
        self.inputs = OfxInputSet()

class OfxMeshEffect(PyObjectWrapper):
    _internal_type_ = OfxMeshEffectInternal

OfxMeshEffectHandle = POINTER(OfxMeshEffect)

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
            kOfxPropertySuite: { 1: OfxPropertySuiteV1() },
            kOfxParameterSuite: { 1: OfxParameterSuiteV1() },
            kOfxMeshEffectSuite: { 1: OfxMeshEffectSuiteV1() },
            kOfxMessageSuite: { 2: OfxMessageSuiteV2() },
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
            raise NotImplemented
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

    def makePropSet(default):
        @staticmethod
        def _propSet(property_set_p, name, component, value):
            print(f"Setting property {name.decode()}[{component}] to {value}")
            property_set = property_set_p.contents.value
            if name not in property_set:
                property_set[name] = [default, default, default, default]
            property_set[name][component] = value
            return kOfxStatOK
        return _propSet

    _propSetDouble = makePropSet(0.0)
    _propSetString = makePropSet("")
    _propSetInt = makePropSet(0)
    _propSetPointer = makePropSet(None)

    def makePropGet(default):
        @staticmethod
        def _propGet(property_set_p, name, component, value_p):
            property_set = property_set_p.contents.value
            if name not in property_set:
                property_set[name] = [default, default, default, default]
            value_p[0] = property_set[name][component]
            print(f"Getting property {name.decode()}[{component}] = {value_p[0]}")
            return kOfxStatOK
        return _propGet

    _propGetDouble = makePropGet(0.0)
    _propGetString = makePropGet("")
    _propGetInt = makePropGet(0)
    _propGetPointer = makePropGet(None)


class OfxParameterSuiteV1(Structure, OfxSuite):
    _fields_ = [
        ("paramDefine",            CFUNCTYPE(OfxStatus, OfxParamSetHandle, c_char_p, c_char_p, POINTER(OfxPropertySetHandle))),
        ("paramGetHandle",         CFUNCTYPE(OfxStatus, OfxParamSetHandle, c_char_p, POINTER(OfxParamHandle), POINTER(OfxPropertySetHandle))),
        ("paramSetGetPropertySet", CFUNCTYPE(OfxStatus, c_int)),
        ("paramGetPropertySet",    CFUNCTYPE(OfxStatus, c_int)),
        ("paramGetValue",          CFUNCTYPE(OfxStatus, OfxParamHandle, c_void_p)),
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
        param_set[name] = OfxParamInternal(name, param_type)
        if property_set_pp:
            property_set_pp.contents.contents = to_handle(param_set[name].properties)
        return kOfxStatOK

    @staticmethod
    def _paramGetHandle(param_set_p, name, param_pp, property_set_pp):
        print(f"Getting parameter '{name.decode()}'")
        if not param_set_p:
            print("Invalid parameter set!")
            return kOfxStatErrBadHandle

        param_set = param_set_p.contents.value

        if name not in param_set:
            print("Parameter not found!")
            return kOfxStatErrUnknown

        param_pp.contents.contents = OfxParam(param_set[name])

        if property_set_pp:
            property_set_pp.contents.contents = to_handle(param_set[name].properties)
        return kOfxStatOK

    @staticmethod
    def _paramGetValue(param_p, value_p):
        param = param_p.contents.internal
        print(f"Getting parameter value for '{param.name.decode()}' (= {param.value})")
        target_type, target_count = {
            kOfxParamTypeInteger:    (c_int,    1),
            kOfxParamTypeDouble:     (c_double, 1),
            kOfxParamTypeBoolean:    (c_bool,   1),
            kOfxParamTypeChoice:     (c_int,    1),
            kOfxParamTypeRGBA:       (c_double, 4),
            kOfxParamTypeRGB:        (c_double, 3),
            kOfxParamTypeDouble2D:   (c_double, 2),
            kOfxParamTypeInteger2D:  (c_int,    2),
            kOfxParamTypeDouble3D:   (c_double, 3),
            kOfxParamTypeInteger3D:  (c_double, 3),
            kOfxParamTypeString:     (c_char_p, 1),
            kOfxParamTypeCustom:     (c_int,    1),
            kOfxParamTypeGroup:      (c_int,    1),
            kOfxParamTypePage:       (c_int,    1),
            kOfxParamTypePushButton: (c_int,    1),
        }[param.type]
        typed_value_p = cast(value_p, POINTER(target_type))

        for i in range(target_count):
            typed_value_p[i] = param.value[i]

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
        ("inputReleaseMesh",      CFUNCTYPE(OfxStatus, OfxMeshHandle)),
        ("attributeDefine",       CFUNCTYPE(OfxStatus, c_int)),
        ("meshGetAttribute",      CFUNCTYPE(OfxStatus, OfxMeshHandle, c_char_p, c_char_p, POINTER(OfxPropertySetHandle))),
        ("meshGetPropertySet",    CFUNCTYPE(OfxStatus, c_int)),
        ("meshAlloc",             CFUNCTYPE(OfxStatus, OfxMeshHandle)),
        ("abort",                 CFUNCTYPE(OfxStatus, c_int)),
    ]

    def __init__(self):
        self.initFunctionPointers()

    @staticmethod
    def _getParamSet(mesh_effect_p, param_set_pp):
        mesh_effect = mesh_effect_p.contents.internal
        print(f"Getting parameter set from mesh {mesh_effect}")
        cast(param_set_pp, c_void_p)  # for some reason this line is required
        param_set_pp.contents.contents = to_handle(mesh_effect.params)
        return kOfxStatOK

    @staticmethod
    def _inputDefine(mesh_effect_p, name, input_pp, input_props_pp):
        print(f"Defining input '{name.decode()}'")
        mesh_effect = mesh_effect_p.contents.internal

        mesh_input_internal = OfxMeshInputInternal(name)
        mesh_effect.inputs[name] = mesh_input_internal

        cast(input_pp, c_void_p)  # for some reason this line is required
        input_pp.contents.contents = OfxMeshInput(mesh_input_internal)

        if input_props_pp:
            cast(input_props_pp, c_void_p)  # for some reason this line is required
            input_props_pp.contents.contents = to_handle(mesh_input_internal.properties)

        return kOfxStatOK

    @staticmethod
    def _inputGetHandle(mesh_effect_p, name, input_pp, input_props_pp):
        print(f"Getting input '{name.decode()}'")
        mesh_effect = mesh_effect_p.contents.internal

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
        mesh_input = mesh_input_p.contents.internal

        mesh = mesh_input.mesh

        cast(mesh_pp, c_void_p)  # for some reason this line is required
        mesh_pp.contents.contents = OfxMesh(mesh)

        if mesh_props_pp:
            cast(mesh_props_pp, c_void_p)  # for some reason this line is required
            mesh_props_pp.contents.contents = to_handle(mesh.properties)

        return kOfxStatOK

    @staticmethod
    def _inputReleaseMesh(mesh_p):
        print(f"Releasing mesh")
        # The GC will de the job anyways
        return kOfxStatOK

    @staticmethod
    def _meshGetAttribute(mesh_p, attachment, name, attribute_pp):
        print(f"Getting {attachment.decode()} attribute '{name.decode()}'")
        mesh = mesh_p.contents.internal
        attribute = mesh.attributes.get(attachment, {}).get(name)
        if attribute is None:
            print(f"Attribute does not exist: {attachment.decode()}/{name.decode()}")
            return kOfxStatErrBadIndex

        cast(attribute_pp, c_void_p)  # for some reason this line is required
        attribute_pp.contents.contents = to_handle(attribute)
        return kOfxStatOK

    @staticmethod
    def _meshAlloc(mesh_p):
        mesh = mesh_p.contents.internal
        print(f"Allocating mesh data for {mesh.point_count} points, {mesh.corner_count} corners and {mesh.face_count} faces")
        mesh.allocate()
        return kOfxStatOK

class OfxMessageSuiteV2(Structure, OfxSuite):
    _fields_ = [
        ("message",                CFUNCTYPE(OfxStatus, c_int)),
        ("setPersistentMessage",   CFUNCTYPE(OfxStatus, c_int)),
        ("clearPersistentMessage", CFUNCTYPE(OfxStatus, c_int)),
    ]

    def __init__(self):
        self.initFunctionPointers()

class OfxPluginLibrary:
    def __init__(self, dll_filename):
        hllDll = CDLL(dll_filename)
        hllApiProto = CFUNCTYPE(c_int)
        hllApiParams = ()
        self.OfxGetNumberOfPlugins = hllApiProto(("OfxGetNumberOfPlugins", hllDll), hllApiParams)

        hllApiProto = CFUNCTYPE(POINTER(OfxPlugin), c_int)
        hllApiParams = ((1, "nth", 0),)
        self.OfxGetPlugin = hllApiProto(("OfxGetPlugin", hllDll), hllApiParams)

def main(dll_filename):
    host = OfxHost()
    lib = OfxPluginLibrary(dll_filename)

    n = lib.OfxGetNumberOfPlugins()
    print(f"Found {n} plugins")
    
    plugin = lib.OfxGetPlugin(0).contents
    print(f"Plugin #0 is called '{plugin.pluginIdentifier.decode()}'")

    plugin.setHost(host)

    status = plugin.mainEntry(kOfxActionLoad, None, None, None)

    descriptor_internal = OfxMeshEffectInternal()
    descriptor = OfxMeshEffect(descriptor_internal)
    status = plugin.mainEntry(kOfxActionDescribe, byref(descriptor), None, None)
    print(f"kOfxActionDescribe status = {status}")

    instance_internal = deepcopy(descriptor_internal)
    instance = OfxMeshEffect(instance_internal)

    status = plugin.mainEntry(kOfxActionCreateInstance, byref(instance), None, None)
    print(f"kOfxActionCreateInstance status = {status}")

    mesh = instance_internal.inputs[kOfxMeshMainInput].mesh
    mesh.point_count = 4
    mesh.corner_count = 6
    mesh.face_count = 2
    mesh.allocate()
    attr = mesh.attributes[kOfxMeshAttribPoint][kOfxMeshAttribPointPosition]
    attr.py_data[:] = (
        (-1.0, -1.0, 0.0),
        (+1.0, -1.0, 0.0),
        (+1.0, +1.0, 0.0),
        (-1.0, +1.0, 0.0),
    )
    attr = mesh.attributes[kOfxMeshAttribCorner][kOfxMeshAttribCornerPoint]
    attr.py_data[:] = (
        0, 1, 2,
        2, 0, 3,
    )
    attr = mesh.attributes[kOfxMeshAttribFace][kOfxMeshAttribFaceSize]
    attr.py_data[:] = (
        3, 3,
    )

    instance_internal.params[b"translation"].value = (0.1, 0.2, 0.3)

    status = plugin.mainEntry(kOfxMeshEffectActionCook, byref(instance), None, None)
    print(f"kOfxActionCook status = {status}")

    output_mesh = instance_internal.inputs[kOfxMeshMainOutput].mesh
    attr = output_mesh.attributes[kOfxMeshAttribPoint][kOfxMeshAttribPointPosition]
    print(tuple(attr.py_data[0]))

#main(r"E:\SourceCode\MfxCascade\build\MfxCascade.ofx.bundle\Win64\MfxCascade.ofx")
main(r"E:\SourceCode\MfxExamples\build\Release\mfx_examples.ofx")
