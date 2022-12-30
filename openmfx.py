import ctypes.wintypes
from ctypes import (
    CFUNCTYPE, POINTER, CDLL, c_char_p, c_int, c_uint, c_void_p, c_double, c_float, c_bool,
    Structure, pointer, cast, py_object, addressof, byref, c_ubyte, sizeof
)
import random
import sys
from copy import deepcopy

to_handle = py_object

class OfxConstants:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

constants = OfxConstants(
StatOK = 0,
StatFailed = 1,
StatErrFatal = 2,
StatErrUnknown = 3,
StatErrMissingHostFeature = 4,
StatErrUnsupported = 5,
StatErrExists = 6,
StatErrFormat = 7,
StatErrMemory = 8,
StatErrBadHandle = 9,
StatErrBadIndex = 10,
StatErrValue = 11,
StatReplyYes = 12,
StatReplyNo = 13,
StatReplyDefault = 14,

MeshEffectPluginAPI = b"OfxMeshEffectPluginAPI",

MeshAttribPoint = b"OfxMeshAttribPoint",
MeshAttribCorner = b"OfxMeshAttribCorner",
MeshAttribFace = b"OfxMeshAttribFace",
MeshAttribMesh = b"OfxMeshAttribMesh",

MeshAttribPointPosition = b"OfxMeshAttribPointPosition",
MeshAttribCornerPoint = b"OfxMeshAttribCornerPoint",
MeshAttribFaceSize = b"OfxMeshAttribFaceSize",

MeshAttribTypeUByte = b"OfxMeshAttribTypeUByte",
MeshAttribTypeInt = b"OfxMeshAttribTypeInt",
MeshAttribTypeFloat = b"OfxMeshAttribTypeFloat",

MeshAttribPropData = b"OfxMeshAttribPropData",
MeshAttribPropIsOwner = b"OfxMeshAttribPropIsOwner",
MeshAttribPropStride = b"OfxMeshAttribPropStride",
MeshAttribPropComponentCount = b"OfxMeshAttribPropComponentCount",
MeshAttribPropType = b"OfxMeshAttribPropType",
MeshAttribPropSemantic = b"OfxMeshAttribPropSemantic",

MeshMainInput = b"OfxMeshMainInput",
MeshMainOutput = b"OfxMeshMainOutput",

MeshPropPointCount = b"OfxMeshPropPointCount",
MeshPropCornerCount = b"OfxMeshPropCornerCount",
MeshPropFaceCount = b"OfxMeshPropFaceCount",

ActionLoad = b"OfxActionLoad",
ActionDescribe = b"OfxActionDescribe",
ActionCreateInstance = b"OfxActionCreateInstance",
ActionDestroyInstance = b"OfxActionDestroyInstance",
MeshEffectActionCook = b"OfxMeshEffectActionCook",

PropertySuite = b"OfxPropertySuite",
ParameterSuite = b"OfxParameterSuite",
MeshEffectSuite = b"OfxMeshEffectSuite",
MessageSuite = b"OfxMessageSuite",

ParamTypeInteger = b"OfxParamTypeInteger",
ParamTypeDouble = b"OfxParamTypeDouble",
ParamTypeBoolean = b"OfxParamTypeBoolean",
ParamTypeChoice = b"OfxParamTypeChoice",
ParamTypeRGBA = b"OfxParamTypeRGBA",
ParamTypeRGB = b"OfxParamTypeRGB",
ParamTypeDouble2D = b"OfxParamTypeDouble2D",
ParamTypeInteger2D = b"OfxParamTypeInteger2D",
ParamTypeDouble3D = b"OfxParamTypeDouble3D",
ParamTypeInteger3D = b"OfxParamTypeInteger3D",
ParamTypeString = b"OfxParamTypeString",
ParamTypeCustom = b"OfxParamTypeCustom",
ParamTypeGroup = b"OfxParamTypeGroup",
ParamTypePage = b"OfxParamTypePage",
ParamTypePushButton = b"OfxParamTypePushButton",

ParamPropDefault = b"OfxParamPropDefault",
)

kOfx = constants

OfxStatus = c_int
OfxTime = c_double
OfxPropertySet = dict
OfxPropertySetHandle = POINTER(py_object)

OfxParamSet = dict
OfxParamSetHandle = POINTER(py_object)

OfxInputSet = dict
OfxInputSetHandle = POINTER(py_object)

class PyObjectWrapper(Structure):
    """
    User-exposed types generally are simple handles, pointers to actual
    internal structures.
    These handle derive from PyObjectWrapper and set _internal_type_ to the
    underlying data structure.
    """
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

    def __repr__(self):
        return f"<OfxParam '{self.name.decode()}'>"

class OfxParam(PyObjectWrapper):
    _internal_type_ = OfxParamInternal

OfxParamHandle = POINTER(OfxParam)

class OfxAttribute(OfxPropertySet):
    def __init__(self, name, attachment, component_count, attribute_type):
        self.name = name
        self.attachment = attachment
        self.py_data = None  # python reference to the data buffer, to have the GC manage it

        self[kOfx.MeshAttribPropData] = [None]
        self[kOfx.MeshAttribPropIsOwner] = [True]
        self[kOfx.MeshAttribPropStride] = [-1]
        self[kOfx.MeshAttribPropComponentCount] = [component_count]
        self[kOfx.MeshAttribPropType] = [attribute_type]
        self[kOfx.MeshAttribPropSemantic] = [None]

    def allocate(self, item_count):
        if not self.is_owner:
            return

        if self.py_data is not None:
            raise Exception("Attribute already allocated")

        component_type = {
            kOfx.MeshAttribTypeFloat: c_float,
            kOfx.MeshAttribTypeInt: c_int,
            kOfx.MeshAttribTypeUByte: c_ubyte,
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
        return self[kOfx.MeshAttribPropData][0]

    @data.setter
    def data(self, value):
        self[kOfx.MeshAttribPropData] = [value]

    @property
    def is_owner(self):
        return self[kOfx.MeshAttribPropIsOwner][0]

    @is_owner.setter
    def is_owner(self, value):
        self[kOfx.MeshAttribPropIsOwner] = [value]

    @property
    def stride(self):
        return self[kOfx.MeshAttribPropStride][0]

    @stride.setter
    def stride(self, value):
        self[kOfx.MeshAttribPropStride] = [value]

    @property
    def component_count(self):
        return self[kOfx.MeshAttribPropComponentCount][0]

    @component_count.setter
    def component_count(self, value):
        self[kOfx.MeshAttribPropComponentCount] = [value]

    @property
    def attribute_type(self):
        return self[kOfx.MeshAttribPropType][0]

    @attribute_type.setter
    def attribute_type(self, value):
        self[kOfx.MeshAttribPropType] = [value]

    @property
    def semantic(self):
        return self[kOfx.MeshAttribPropSemantic][0]

    @semantic.setter
    def semantic(self, value):
        self[kOfx.MeshAttribPropSemantic] = [value]
    

class OfxMeshInternal:
    def __init__(self):
        self.properties = OfxPropertySet()
        self.attributes = {
            kOfx.MeshAttribPoint: {
                kOfx.MeshAttribPointPosition: OfxAttribute(kOfx.MeshAttribPointPosition, kOfx.MeshAttribPoint, 3, kOfx.MeshAttribTypeFloat)
            },
            kOfx.MeshAttribCorner: {
                kOfx.MeshAttribCornerPoint: OfxAttribute(kOfx.MeshAttribCornerPoint, kOfx.MeshAttribCorner, 1, kOfx.MeshAttribTypeInt)
            },
            kOfx.MeshAttribFace: {
                kOfx.MeshAttribFaceSize: OfxAttribute(kOfx.MeshAttribFaceSize, kOfx.MeshAttribFace, 1, kOfx.MeshAttribTypeInt)
            }
        }
        self.point_count = 0
        self.corner_count = 0
        self.face_count = 0

    def __repr__(self):
        return f"<OfxMesh data at {'{:#018x}'.format(id(self))}>"

    def allocate(self):
        type_to_count = {
            kOfx.MeshAttribPoint: kOfx.MeshPropPointCount,
            kOfx.MeshAttribCorner: kOfx.MeshPropCornerCount,
            kOfx.MeshAttribFace: kOfx.MeshPropFaceCount,
        }
        for item_type, attr_per_item in self.attributes.items():
            item_count = self.properties[type_to_count[item_type]][0]
            for attr in attr_per_item.values():
                attr.allocate(item_count)

    @property
    def point_count(self):
        return self.properties[kOfx.MeshPropPointCount][0]

    @point_count.setter
    def point_count(self, value):
        self.properties[kOfx.MeshPropPointCount] = [value]

    @property
    def corner_count(self):
        return self.properties[kOfx.MeshPropCornerCount][0]

    @corner_count.setter
    def corner_count(self, value):
        self.properties[kOfx.MeshPropCornerCount] = [value]

    @property
    def face_count(self):
        return self.properties[kOfx.MeshPropFaceCount][0]

    @face_count.setter
    def face_count(self, value):
        self.properties[kOfx.MeshPropFaceCount] = [value]
        

class OfxMesh(PyObjectWrapper):
    _internal_type_ = OfxMeshInternal

OfxMeshHandle = POINTER(OfxMesh)

class OfxMeshInputInternal:
    def __init__(self, name):
        self.name = name
        self.properties = OfxPropertySet()
        self.mesh = OfxMeshInternal()
        self.requested_attributes = {
            kOfx.MeshAttribPoint: {},
            kOfx.MeshAttribCorner: {},
            kOfx.MeshAttribFace: {}
        }

    def __repr__(self):
        return f"<OfxMeshInput '{self.name.decode()}'>"

class OfxMeshInput(PyObjectWrapper):
    _internal_type_ = OfxMeshInputInternal

OfxMeshInputHandle = POINTER(OfxMeshInput)

class OfxMeshEffectInternal:
    def __init__(self):
        self.params = OfxParamSet()
        self.inputs = OfxInputSet()

    def __repr__(self):
        return f"<OfxMeshEffect data at {'{:#018x}'.format(id(self))}>"

class OfxMeshEffect(PyObjectWrapper):
    _internal_type_ = OfxMeshEffectInternal

OfxMeshEffectHandle = POINTER(OfxMeshEffect)

class OfxHost(Structure):
    """
    Represents the host software, and contain all function suites
    """
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
            kOfx.PropertySuite: { 1: OfxPropertySuiteV1() },
            kOfx.ParameterSuite: { 1: OfxParameterSuiteV1() },
            kOfx.MeshEffectSuite: { 1: OfxMeshEffectSuiteV1() },
            kOfx.MessageSuite: { 2: OfxMessageSuiteV2() },
        }

    @staticmethod
    @CFUNCTYPE(c_void_p, OfxPropertySetHandle, c_char_p, c_int)
    def _fetchSuite(host_props_p, suite_name, suite_version):
        host_props = host_props_p.contents.value
        self = host_props['host_instance']
        print(f"Fetching suite {suite_name.decode()}, version {suite_version}")
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
    """
    A plugin as returned by the OfxGetPlugin API call
    """
    _fields_ = [
        ("pluginApi", c_char_p),
        ("apiVersion", c_int),
        ("pluginIdentifier", c_char_p),
        ("pluginVersionMajor", c_uint),
        ("pluginVersionMinor", c_uint),
        ("setHost", CFUNCTYPE(None, POINTER(OfxHost))),
        ("mainEntry", CFUNCTYPE(OfxStatus, c_char_p, c_void_p, OfxPropertySetHandle, OfxPropertySetHandle)),
    ]

    def __repr__(self):
        return f"<OfxPlugin '{self.pluginIdentifier.decode()}' v{self.pluginVersionMajor}.{self.pluginVersionMinor}>"

class OfxSuite:
    """
    Parent class for function suites, which defines a default implementation
    for all functions 'foo' declared in _fields_ but for which no method
    _foo exists.
    """
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
            return kOfx.StatOK
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
            return kOfx.StatOK
        return _propSet

    _propSetDouble = makePropSet(0.0)
    _propSetString = makePropSet("")
    _propSetInt = makePropSet(0)
    _propSetPointer = makePropSet(None)

    def makePropGet(default):
        @staticmethod
        def _propGet(property_set_p, name, component, value_p):
            if not property_set_p:
                print("Null property set!")
                return kOfx.StatErrBadHandle
            property_set = property_set_p.contents.value
            if name not in property_set:
                property_set[name] = [default, default, default, default]
            value_p[0] = property_set[name][component]
            print(f"Getting property {name.decode()}[{component}] = {value_p[0]}")
            return kOfx.StatOK
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
            return kOfx.StatErrBadHandle
        param_set = param_set_p.contents.value
        param_set[name] = OfxParamInternal(name, param_type)
        if property_set_pp:
            property_set_pp.contents.contents = to_handle(param_set[name].properties)
        return kOfx.StatOK

    @staticmethod
    def _paramGetHandle(param_set_p, name, param_pp, property_set_pp):
        print(f"Getting parameter '{name.decode()}'")
        if not param_set_p:
            print("Invalid parameter set!")
            return kOfx.StatErrBadHandle

        param_set = param_set_p.contents.value

        if name not in param_set:
            print("Parameter not found!")
            return kOfx.StatErrUnknown

        param_pp.contents.contents = OfxParam(param_set[name])

        if property_set_pp:
            property_set_pp.contents.contents = to_handle(param_set[name].properties)
        return kOfx.StatOK

    @staticmethod
    def _paramGetValue(param_p, value_p):
        param = param_p.contents.internal
        print(f"Getting parameter value for '{param.name.decode()}' (= {param.value})")
        target_type, target_count = {
            kOfx.ParamTypeInteger:    (c_int,    1),
            kOfx.ParamTypeDouble:     (c_double, 1),
            kOfx.ParamTypeBoolean:    (c_bool,   1),
            kOfx.ParamTypeChoice:     (c_int,    1),
            kOfx.ParamTypeRGBA:       (c_double, 4),
            kOfx.ParamTypeRGB:        (c_double, 3),
            kOfx.ParamTypeDouble2D:   (c_double, 2),
            kOfx.ParamTypeInteger2D:  (c_int,    2),
            kOfx.ParamTypeDouble3D:   (c_double, 3),
            kOfx.ParamTypeInteger3D:  (c_double, 3),
            kOfx.ParamTypeString:     (c_char_p, 1),
            kOfx.ParamTypeCustom:     (c_int,    1),
            kOfx.ParamTypeGroup:      (c_int,    1),
            kOfx.ParamTypePage:       (c_int,    1),
            kOfx.ParamTypePushButton: (c_int,    1),
        }[param.type]
        typed_value_p = cast(value_p, POINTER(target_type))

        for i in range(target_count):
            typed_value_p[i] = param.value[i]

        return kOfx.StatOK

class OfxMeshEffectSuiteV1(Structure, OfxSuite):
    _fields_ = [
        ("getPropertySet",          CFUNCTYPE(OfxStatus, c_int)),
        ("getParamSet",             CFUNCTYPE(OfxStatus, OfxMeshEffectHandle, POINTER(OfxParamSetHandle))),
        ("inputDefine",             CFUNCTYPE(OfxStatus, OfxMeshEffectHandle, c_char_p, POINTER(OfxMeshInputHandle), POINTER(OfxPropertySetHandle))),
        ("inputGetHandle",          CFUNCTYPE(OfxStatus, OfxMeshEffectHandle, c_char_p, POINTER(OfxMeshInputHandle), POINTER(OfxPropertySetHandle))),
        ("inputGetPropertySet",     CFUNCTYPE(OfxStatus, c_int)),
        ("inputRequestAttribute",   CFUNCTYPE(OfxStatus, OfxMeshInputHandle, c_char_p, c_char_p, c_int, c_char_p, c_char_p, c_int)),
        ("inputGetMesh",            CFUNCTYPE(OfxStatus, OfxMeshInputHandle, OfxTime, POINTER(OfxMeshHandle), POINTER(OfxPropertySetHandle))),
        ("inputReleaseMesh",        CFUNCTYPE(OfxStatus, OfxMeshHandle)),
        ("attributeDefine",         CFUNCTYPE(OfxStatus, c_int)),
        ("meshGetAttributeByIndex", CFUNCTYPE(OfxStatus, c_int)),
        ("meshGetAttribute",        CFUNCTYPE(OfxStatus, OfxMeshHandle, c_char_p, c_char_p, POINTER(OfxPropertySetHandle))),
        ("meshGetPropertySet",      CFUNCTYPE(OfxStatus, OfxMeshHandle, POINTER(OfxPropertySetHandle))),
        ("meshAlloc",               CFUNCTYPE(OfxStatus, OfxMeshHandle)),
        ("abort",                   CFUNCTYPE(OfxStatus, c_int)),
    ]

    def __init__(self):
        self.initFunctionPointers()

    @staticmethod
    def _getParamSet(mesh_effect_p, param_set_pp):
        mesh_effect = mesh_effect_p.contents.internal
        print(f"Getting parameter set from mesh {mesh_effect}")
        cast(param_set_pp, c_void_p)  # for some reason this line is required
        param_set_pp.contents.contents = to_handle(mesh_effect.params)
        return kOfx.StatOK

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

        return kOfx.StatOK

    @staticmethod
    def _inputGetHandle(mesh_effect_p, name, input_pp, input_props_pp):
        print(f"Getting input '{name.decode()}'")
        mesh_effect = mesh_effect_p.contents.internal

        if name not in mesh_effect.inputs:
            print(f"Input does not exist: '{name.decode()}'")
            return kOfx.StatErrBadIndex

        mesh_input = mesh_effect.inputs[name]

        cast(input_pp, c_void_p)  # for some reason this line is required
        input_pp.contents.contents = to_handle(mesh_input)

        if input_props_pp:
            cast(input_props_pp, c_void_p)  # for some reason this line is required
            input_props_pp.contents.contents = to_handle(mesh_input.properties)

        return kOfx.StatOK

    @staticmethod
    def _inputRequestAttribute(mesh_input_p, attachment, name, component_count, type, semantic, mandatory):
        mesh_input = mesh_input_p.contents.internal
        attributes = mesh_input.requested_attributes[attachment]

        if name in attributes:
            return kOfx.StatErrExists

        print(f"Requesting attribute '{name.decode()}': {component_count} x {type.decode()[17:]}, {semantic.decode()[21:]} ({'mandatory' if mandatory else 'optional'})")
        attributes[name] = (component_count, type, semantic, mandatory)

        return kOfx.StatOK

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

        return kOfx.StatOK

    @staticmethod
    def _inputReleaseMesh(mesh_p):
        print(f"Releasing mesh")
        # The GC will de the job anyways
        return kOfx.StatOK

    @staticmethod
    def _meshGetAttribute(mesh_p, attachment, name, attribute_pp):
        print(f"Getting {attachment.decode()} attribute '{name.decode()}'")
        mesh = mesh_p.contents.internal
        attribute = mesh.attributes.get(attachment, {}).get(name)
        if attribute is None:
            print(f"Attribute does not exist: {attachment.decode()}/{name.decode()}")
            return kOfx.StatErrBadIndex

        cast(attribute_pp, c_void_p)  # for some reason this line is required
        attribute_pp.contents.contents = to_handle(attribute)
        return kOfx.StatOK

    @staticmethod
    def _meshGetPropertySet(mesh_p, mesh_props_pp):
        mesh = mesh_p.contents.internal

        if not mesh_props_pp:
            return kOfx.kOfxStatErrBadHandle

        cast(mesh_props_pp, c_void_p)  # for some reason this line is required
        mesh_props_pp.contents.contents = to_handle(mesh.properties)
        #mesh_props_pp.contents = OfxPropertySetHandle(to_handle(mesh.properties))
        return kOfx.StatOK

    @staticmethod
    def _meshAlloc(mesh_p):
        mesh = mesh_p.contents.internal
        print(f"Allocating mesh data for {mesh.point_count} points, {mesh.corner_count} corners and {mesh.face_count} faces")
        mesh.allocate()
        return kOfx.StatOK

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
        self._hll = CDLL(dll_filename)
        hllApiProto = CFUNCTYPE(c_int)
        hllApiParams = ()
        self.OfxGetNumberOfPlugins = hllApiProto(("OfxGetNumberOfPlugins", self._hll), hllApiParams)

        hllApiProto = CFUNCTYPE(POINTER(OfxPlugin), c_int)
        hllApiParams = ((1, "nth", 0),)
        self.OfxGetPlugin = hllApiProto(("OfxGetPlugin", self._hll), hllApiParams)
        def errcheck(result, func, args):
            return result.contents  # dereferences pointer
        self.OfxGetPlugin.errcheck = errcheck

    def close(self):
        handle = self._hll._handle
        if sys.platform == "win32":
            kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
            kernel32.FreeLibrary.argtypes = [ctypes.wintypes.HMODULE]
            kernel32.FreeLibrary(handle)
        else:
            libdl = ctypes.cdll.LoadLibrary('libdl.so')
            libdl.dlclose(handle)
        self.OfxGetNumberOfPlugins = lambda: 0
        self.OfxGetPlugin = lambda n: None
