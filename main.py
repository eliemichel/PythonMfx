from ctypes import byref
from copy import deepcopy
from openmfx import OfxHost, OfxPluginLibrary, OfxMeshEffectInternal, OfxMeshEffect
from openmfx import constants as kOfx

def main(dll_filename):
    host = OfxHost()
    lib = OfxPluginLibrary(dll_filename)

    n = lib.OfxGetNumberOfPlugins()
    print(f"Found {n} plugins")
    
    plugin = lib.OfxGetPlugin(0).contents
    print(f"Plugin #0 is called '{plugin.pluginIdentifier.decode()}'")

    plugin.setHost(host)

    status = plugin.mainEntry(kOfx.ActionLoad, None, None, None)
    print(f"OfxActionLoad status = {status}")

    py_descriptor = OfxMeshEffectInternal()
    descriptor = OfxMeshEffect(py_descriptor)
    status = plugin.mainEntry(kOfx.ActionDescribe, byref(descriptor), None, None)
    print(f"OfxActionDescribe status = {status}")

    print(f"Effect has {len(py_descriptor.inputs)} inputs/outputs:")
    for input in py_descriptor.inputs.values():
        print(f"  - {input.name.decode()}")

    print(f"Effect has {len(py_descriptor.params)} parameters:")
    for param in py_descriptor.params.values():
        print(f"  - {param.name.decode()} ({param.type})")

    py_instance = deepcopy(py_descriptor)
    instance = OfxMeshEffect(py_instance)
    status = plugin.mainEntry(kOfx.ActionCreateInstance, byref(instance), None, None)
    print(f"OfxActionCreateInstance status = {status}")

    mesh = py_instance.inputs[kOfx.MeshMainInput].mesh
    mesh.point_count = 4
    mesh.corner_count = 6
    mesh.face_count = 2
    mesh.allocate()
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

    py_instance.params[b"translation"].value = (0.1, 0.2, 0.3)

    status = plugin.mainEntry(kOfx.MeshEffectActionCook, byref(instance), None, None)
    print(f"OfxActionCook status = {status}")

    output_mesh = py_instance.inputs[kOfx.MeshMainOutput].mesh
    attr = output_mesh.attributes[kOfx.MeshAttribPoint][kOfx.MeshAttribPointPosition]
    print(tuple(attr.py_data[0]))

#main(r"E:\SourceCode\MfxCascade\build\MfxCascade.ofx.bundle\Win64\MfxCascade.ofx")
main(r"E:\SourceCode\MfxExamples\build\Release\mfx_examples.ofx")
