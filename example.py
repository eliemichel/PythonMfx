from ctypes import byref
from copy import deepcopy
from openmfx import OfxHost, OfxPluginLibrary, OfxMeshEffectInternal, OfxMeshEffect
from openmfx import constants as kOfx

# Adapt to your ofx file
PLUGIN_PATH = r"E:\SourceCode\MfxExamples\build\Debug\mfx_examples.ofx"
PLUGIN_INDEX = 0

def main(ofx_filename, plugin_index):
    # We first create the host, which shall live until the program closes
    # It ensures the communication with plugins
    host = OfxHost()

    # We load a plugin library from an ofx file
    try:
        lib = OfxPluginLibrary(ofx_filename)
    except FileNotFoundError:
        print(
            f"Could not load ofx library! Check that its path '{ofx_filename}'" +
            " is correct and that its dependencies are correct (you may use" +
            " lucasg's Dependencies)")
        exit(1)

    # A library exposes only two symbols: OfxGetNumberOfPlugins and OfxGetPlugin
    n = lib.OfxGetNumberOfPlugins()
    print(f"Found {n} plugins")

    # See https://openfx.readthedocs.io/en/master/Reference/ofxPluginStruct.html
    # for details ebout the fields of the plugin structure
    plugin = lib.OfxGetPlugin(plugin_index)
    print(
        f"Plugin #{plugin_index} is called '{plugin.pluginIdentifier.decode()}' " +
        f"version {plugin.pluginVersionMajor}.{plugin.pluginVersionMinor}"
    )
    
    # A plugin contained in a .ofx file may be a mesh effect or an image effect
    # (for 2D compositing) or maybe even another type of effect, so we must
    # check that this plugin is a mesh effect (and we also check the API
    # version)
    is_supported = plugin.pluginApi == kOfx.MeshEffectPluginAPI and plugin.apiVersion == 1
    if not is_supported:
        print(
            f"Plugin uses an unsupported API: '{plugin.pluginApi.decode()}' " +
            f"version {plugin.apiVersion}"
        )
        exit(1)

    # Before calling any of the plugin's methods, we must point it to the host
    # structure, so that the plugin queries the lists of functions (so called
    # function suites) that it may use from the host.
    plugin.setHost(host)

    # All plugin methods are called through the single entry point 'mainEntry'
    # The method name is the first argument, called the action. The list of
    # arguments depends on the action.
    # All actions return a status among the kOfx.Stat* values.
    # (See https://openmesheffect.org/Reference/ofxMeshEffectActions.html)
    status = plugin.mainEntry(kOfx.ActionLoad, None, None, None)
    print(f"OfxActionLoad status = {status}")
    if status != kOfx.StatOK:
        print("Could not load plugin!")
        exit(1)

    # NB: You will likely want to wrap these calls into higher level functions,
    # but this module only provides a low level API matching the C API as close
    # as possible.

    # Before actually running a mesh effect, we get its descriptor, namelay an
    # object detailing the expected inputs and parameters of the effect.
    # Both descriptors and effect instances are stored in the same structure
    # named OfxMeshEffect.
    # We first build the python object OfxMeshEffectInternal and then provide a
    # shallow handle OfxMeshEffect to the entry point.
    py_descriptor = OfxMeshEffectInternal()
    descriptor = OfxMeshEffect(py_descriptor)
    # We then pass the descriptor handle with `byref` because ActionDescribe
    # expects a pointer to a handle.
    status = plugin.mainEntry(kOfx.ActionDescribe, byref(descriptor), None, None)
    print(f"OfxActionDescribe status = {status}")
    assert(status == kOfx.StatOK)

    # We can now inspect the effect descriptor
    # An effect usually has an input called kOfx.MeshMainInput, potentially
    # extra inputs, and one called kOfx.MeshMainOutput that is the only
    # possible output of the effect.
    print(f"Effect has {len(py_descriptor.inputs)} inputs/outputs:")
    for input in py_descriptor.inputs.values():
        print(f"  - {input.name.decode()}")

    print(f"Effect has {len(py_descriptor.params)} parameters:")
    for param in py_descriptor.params.values():
        print(f"  - {param.name.decode()} ({param.type.decode()[12:]})")

    # An effect instance is created by cloning the descriptor and then calling
    # the ActionCreateInstance action on the instance.
    py_instance = deepcopy(py_descriptor)
    instance = OfxMeshEffect(py_instance)
    status = plugin.mainEntry(kOfx.ActionCreateInstance, byref(instance), None, None)
    print(f"OfxActionCreateInstance status = {status}")
    assert(status == kOfx.StatOK)

    # Before running the effect, we set mesh data for its input, and tune
    # parameter values.
    mesh = py_instance.inputs[kOfx.MeshMainInput].mesh

    # We first set geometric element counts and then allocate buffers
    # NB: We use default attributes only here (position, connectivity)
    # but we could also set before allocation extra attributes, as well as
    # point some attributes to existing data buffers rather than allocating
    # new data.
    mesh.point_count = 4
    mesh.corner_count = 6
    mesh.face_count = 2
    mesh.allocate()

    # Once allocated, we fill in input buffers
    attr = mesh.attributes[kOfx.MeshAttribPoint][kOfx.MeshAttribPointPosition]
    attr.py_data[:] = (
        (-1.0, -1.0, 0.0),
        (+1.0, -1.0, 0.0),
        (+1.0, +1.0, 0.0),
        (-1.0, +1.0, 0.0),
    )
    attr = mesh.attributes[kOfx.MeshAttribCorner][kOfx.MeshAttribCornerPoint]
    attr.py_data[:] = (
        0, 1, 2,
        2, 0, 3,
    )
    attr = mesh.attributes[kOfx.MeshAttribFace][kOfx.MeshAttribFaceSize]
    attr.py_data[:] = (
        3, 3,
    )

    # Set parameter values
    translation = (0.1, 0.2, 0.3)
    py_instance.params[b"translation"].value = translation

    # We can now run the core cook action, which comptes the effect's output
    status = plugin.mainEntry(kOfx.MeshEffectActionCook, byref(instance), None, None)
    print(f"OfxActionCook status = {status}")
    assert(status == kOfx.StatOK)

    # Read output mesh
    output_mesh = py_instance.inputs[kOfx.MeshMainOutput].mesh
    point_position_attr = output_mesh.attributes[kOfx.MeshAttribPoint][kOfx.MeshAttribPointPosition]
    point_position_data = point_position_attr.py_data
    point0_position = tuple(point_position_data[0])
    print(f"New position of point #0: {point0_position}")

    # Check that the effect computed a translation by (0.1, 0.2, 0.3)
    def is_close(a, b):
        return abs(b - a) < 1e-5
    input_point_position_data = mesh.attributes[kOfx.MeshAttribPoint][kOfx.MeshAttribPointPosition].py_data
    assert(len(input_point_position_data) == len(point_position_data))
    for i, (in_point, out_point) in enumerate(zip(input_point_position_data, point_position_data)):
        for k in range(3):
            assert(is_close(out_point[k], in_point[k] + translation[k]))


main(PLUGIN_PATH, PLUGIN_INDEX)
