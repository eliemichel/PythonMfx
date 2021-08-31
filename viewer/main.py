# This file is part of Python 3D Viewer
#
# Copyright (c) 2020 -- Élie Michel <elie.michel@exppad.com>
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to
# deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# The Software is provided "as is", without warranty of any kind, express or
# implied, including but not limited to the warranties of merchantability,
# fitness for a particular purpose and non-infringement. In no event shall the
# authors or copyright holders be liable for any claim, damages or other
# liability, whether in an action of contract, tort or otherwise, arising
# from, out of or in connection with the software or the use or other dealings
# in the Software.

import moderngl
import struct
import glfw
import imgui
import numpy as np

from augen import App, Camera
from augen.mesh import ObjMesh, RenderedMesh, Mesh

# Add project root to module path
import sys
from os.path import realpath, dirname
sys.path.append(dirname(dirname(realpath(__file__))))

from openmfx import OfxHost, OfxPluginLibrary, OfxMeshEffectInternal, OfxMeshEffect, OfxMeshInternal
from openmfx import constants as kOfx

import ctypes
from ctypes import byref
from copy import deepcopy

default_param_value = {
    kOfx.ParamTypeInteger: 0,
    kOfx.ParamTypeDouble: 0.0,
    kOfx.ParamTypeBoolean: False,
    kOfx.ParamTypeChoice: 0,
    kOfx.ParamTypeRGBA: (0.0, 0.0, 0.0, 1.0),
    kOfx.ParamTypeRGB: (0.0, 0.0, 0.0),
    kOfx.ParamTypeDouble2D: (0.0, 0.0),
    kOfx.ParamTypeInteger2D: (0, 0),
    kOfx.ParamTypeDouble3D: (0.0, 0.0, 0.0),
    kOfx.ParamTypeInteger3D: (0, 0, 0),
    kOfx.ParamTypeString: "",
    kOfx.ParamTypeCustom: 0,
    kOfx.ParamTypeGroup: 0,
    kOfx.ParamTypePage: 0,
    kOfx.ParamTypePushButton: 0,
}

class MyApp(App):
    def init(self):
        ctx = self.ctx
        # Load a mesh
        self.mesh = ObjMesh("sample-data/dragon.obj")

        # Load the glsl program
        self.program = ctx.program(
            vertex_shader=open("shaders/mesh.vert.glsl").read(),
            fragment_shader=open("shaders/mesh.frag.glsl").read(),
        )

        # Create the rendered mesh from the mesh and the program
        self.rendered_mesh = RenderedMesh(ctx, self.mesh, self.program)

        # Setup camera
        w, h = self.size()
        self.camera = Camera(w, h)

        # Initialize some value used in the UI
        self.some_slider = 0.42
        self.plugin_library_path = r"E:\SourceCode\MfxExamples\build\Release\mfx_examples.ofx"

        # OpenMfx
        self.host = OfxHost()
        self.lib = None
        self.current_plugin_index = -1
        self.plugin = None
        self.plugin_loaded = False
        self.descriptor = None
        self.instance = None
        self.parameter_changed = False
        self.input_mesh = None

    def update(self, time, delta_time):
        # Update damping effect (and internal matrices)
        self.camera.update(time, delta_time)

        if self.parameter_changed:
            self.cook()

    def render(self):
        ctx = self.ctx
        self.camera.set_uniforms(self.program)

        ctx.screen.clear(1.0, 1.0, 1.0, -1.0)

        ctx.enable_only(moderngl.DEPTH_TEST | moderngl.CULL_FACE)
        self.rendered_mesh.render(ctx)

    def on_key(self, key, scancode, action, mods):
        if key == glfw.KEY_ESCAPE:
            self.should_close()

    def on_mouse_move(self, x, y):
        self.camera.update_rotation(x, y)

    def on_mouse_button(self, button, action, mods):
        if action == glfw.PRESS and button == glfw.MOUSE_BUTTON_LEFT:
            x, y = self.mouse_pos()
            self.camera.start_rotation(x, y)
        if action == glfw.RELEASE and button == glfw.MOUSE_BUTTON_LEFT:
            self.camera.stop_rotation()

    def on_resize(self, width, height):
        self.camera.resize(width, height)
        self.ctx.viewport = (0, 0, width, height)

    def on_scroll(self, x, y):
        self.camera.zoom(y)

    def ui(self):
        """Use the imgui module here to draw the UI"""
        if imgui.begin_main_menu_bar():
            self.ui_main_menu()
            imgui.end_main_menu_bar()

        imgui.begin("Plugin Library", True)
        self.ui_plugin_library()
        imgui.end()

        imgui.begin("Plugin", True)
        self.ui_plugin()
        imgui.end()

        imgui.begin("Effect Instance", True)
        self.ui_effect_instance()
        imgui.end()

    def ui_main_menu(self):
        if imgui.begin_menu("File", True):

            clicked_quit, selected_quit = imgui.menu_item(
                "Quit", 'Esc', False, True
            )

            if clicked_quit:
                self.should_close()

            imgui.end_menu()

    def ui_plugin_library(self):
        if imgui.button("..."):
            print("Browse...")
        imgui.same_line()
        changed, self.plugin_library_path = imgui.input_text(
            "Path", self.plugin_library_path, 1024,
        )

        if imgui.button("Load"):
            self.load_plugin_library()

        if self.lib is None:
            return

        imgui.same_line()
        if imgui.button("Unload"):
            self.unload_plugin_library()

        if self.lib is None:
            return

        n = self.lib.OfxGetNumberOfPlugins()
        imgui.text(f"Found {n} plugins:")
        all_idents = []
        for i in range(n):
            plugin = self.lib.OfxGetPlugin(i).contents
            ident = plugin.pluginIdentifier.decode()
            #imgui.bullet_text(f"{ident}")
            all_idents.append(ident)

        clicked, new_current_plugin_index = imgui.listbox(
            "", self.current_plugin_index, all_idents, len(all_idents) + 1
        )
        if clicked:
            self.set_current_plugin(new_current_plugin_index)

    def ui_plugin(self):
        if self.plugin is None:
            imgui.text("Load a plugin library and select a plugin...")
            return

        imgui.text(f"Plugin '{self.plugin.pluginIdentifier.decode()}'")
        if imgui.button("Load"):
            self.load_plugin()

        if not self.plugin_loaded:
            return

        imgui.same_line()
        if imgui.button("Unload"):
            self.unload_plugin()

        if not self.plugin_loaded:
            return

        if imgui.button("Describe"):
            self.describe_plugin()

        if self.descriptor is None:
            return

        py_descriptor = self.descriptor.internal
        imgui.text(f"Effect has {len(py_descriptor.inputs)} inputs/outputs:")
        for input in py_descriptor.inputs.values():
            imgui.bullet_text(f"{input.name.decode()}")

        imgui.text(f"Effect has {len(py_descriptor.params)} parameters:")
        for param in py_descriptor.params.values():
            imgui.bullet_text(f"{param.name.decode()} ({param.type.decode()[12:]})")

        if imgui.button("Create Instance"):
            self.create_instance()

        if self.instance is not None:
            imgui.same_line()
            if imgui.button("Destroy Instance"):
                self.destroy_instance()

    def ui_effect_instance(self):
        if self.instance is None:
            imgui.text("Load and describe a plugin to be able to create an instance...")
            return
        
        imgui.text("Parameters:")
        py_instance = self.instance.internal
        self.parameter_changed = False
        for param in py_instance.params.values():
            label = param.name.decode()
            if param.type == kOfx.ParamTypeInteger:
                changed, param.value = imgui.drag_int(label, param.value)
            elif param.type == kOfx.ParamTypeDouble:
                #imgui.slider_float(param.name, param.value, min_value, max_value)
                changed, param.value = imgui.drag_float(label, param.value)
            elif param.type == kOfx.ParamTypeBoolean:
                changed, param.value = imgui.checkbox(label, param.value)
            elif param.type == kOfx.ParamTypeChoice:
                options = ["foo", "bar"]
                clicked, param.value = imgui.combo(label, param.value, options)
            elif param.type == kOfx.ParamTypeRGBA:
                changed, param.value = imgui.color_edit4(label, *param.value)
            elif param.type == kOfx.ParamTypeRGB:
                changed, param.value = imgui.color_edit3(label, *param.value)
            elif param.type == kOfx.ParamTypeDouble2D:
                changed, param.value = imgui.drag_float2(label, *param.value)
            elif param.type == kOfx.ParamTypeInteger2D:
                changed, param.value = imgui.drag_int2(label, *param.value)
            elif param.type == kOfx.ParamTypeDouble3D:
                changed, param.value = imgui.drag_float3(label, *param.value)
            elif param.type == kOfx.ParamTypeInteger3D:
                changed, param.value = imgui.drag_int3(label, *param.value)
            elif param.type == kOfx.ParamTypeString:
                changed, param.value = imgui.input_text(label, param.value, 1024)
            elif param.type == kOfx.ParamTypeCustom:
                imgui.bullet_text(f"{label} ({param.type.decode()[12:]})")
            elif param.type == kOfx.ParamTypeGroup:
                imgui.bullet_text(f"{label} ({param.type.decode()[12:]})")
            elif param.type == kOfx.ParamTypePage:
                imgui.bullet_text(f"{label} ({param.type.decode()[12:]})")
            elif param.type == kOfx.ParamTypePushButton:
                changed = imgui.button(label)
            self.parameter_changed = self.parameter_changed or changed

    def unload_plugin_library(self):
        self.unload_plugin()
        if self.lib is not None:
            self.lib.close()
            self.lib = None
            self.unload_plugin()
            self.plugin = None

    def load_plugin_library(self):
        self.unload_plugin_library()
        self.lib = OfxPluginLibrary(self.plugin_library_path)
        self.current_plugin_index = -1

    def unload_plugin(self):
        self.destroy_instance()
        if self.plugin_loaded:
            status = self.plugin.mainEntry(kOfx.ActionLoad, None, None, None)
        self.plugin_loaded = False
        self.descriptor = None

    def load_plugin(self):
        if self.plugin is None:
            return
        status = self.plugin.mainEntry(kOfx.ActionLoad, None, None, None)
        self.plugin_loaded = status == kOfx.StatOK

    def describe_plugin(self):
        py_descriptor = OfxMeshEffectInternal()
        self.descriptor = OfxMeshEffect(py_descriptor)
        status = self.plugin.mainEntry(kOfx.ActionDescribe, byref(self.descriptor), None, None)
        if status != kOfx.StatOK:
            print(f"Could not describe effect: {status}")
            self.descriptor = None

    def destroy_instance(self):
        if self.instance is None:
            return
        status = self.plugin.mainEntry(kOfx.ActionDestroyInstance, byref(self.instance), None, None)
        print(f"OfxActionCreateInstance status = {status}")
        self.instance = None

    def create_instance(self):
        if self.descriptor is None:
            return
        self.destroy_instance()
        py_descriptor = self.descriptor.internal
        py_instance = deepcopy(py_descriptor)

        for param in py_instance.params.values():
            if kOfx.ParamPropDefault in param.properties:
                param.value = deepcopy(param.properties[kOfx.ParamPropDefault])
            else:
                param.value = deepcopy(default_param_value[param.type])

        self.instance = OfxMeshEffect(py_instance)
        status = self.plugin.mainEntry(kOfx.ActionCreateInstance, byref(self.instance), None, None)
        if status != kOfx.StatOK:
            print(f"Could not create effect instance: {status}")
            self.instance = None

    def set_current_plugin(self, plugin_index):
        if self.current_plugin_index == plugin_index:
            return
        self.unload_plugin()
        self.current_plugin_index = plugin_index
        self.plugin = self.lib.OfxGetPlugin(plugin_index).contents
        self.plugin.setHost(self.host)

    def cook(self):
        if self.instance is None:
            return

        self.ensure_input_mesh()
        py_instance = self.instance.internal
        py_instance.inputs[kOfx.MeshMainInput].mesh = self.input_mesh

        status = self.plugin.mainEntry(kOfx.MeshEffectActionCook, byref(self.instance), None, None)
        print(f"OfxActionCook status = {status}")

        output_mesh = py_instance.inputs[kOfx.MeshMainOutput].mesh
        py_instance.inputs[kOfx.MeshMainOutput].mesh = OfxMeshInternal()

        # TODO: optimize this
        print(f"Output mesh: {output_mesh.point_count} points, {output_mesh.corner_count} corners and {output_mesh.face_count} faces")
        P = np.empty((output_mesh.corner_count, 3), dtype=float)
        N = np.empty((output_mesh.corner_count, 3), dtype=float)
        point_attr = output_mesh.attributes[kOfx.MeshAttribPoint][kOfx.MeshAttribPointPosition]
        corner_attr = output_mesh.attributes[kOfx.MeshAttribCorner][kOfx.MeshAttribCornerPoint]
        point_attr_data = ctypes.cast(point_attr.data, ctypes.POINTER(ctypes.c_float * 3))
        corner_attr_data = ctypes.cast(corner_attr.data, ctypes.POINTER(ctypes.c_int))
        assert(output_mesh.corner_count >= 3 * output_mesh.face_count)
        for f in range(output_mesh.face_count):
            for c in range(3):
                index = corner_attr_data[3 * f + c]
                P[3 * f + c] = point_attr_data[index]
            A = P[3 * f + 0]
            AB = P[3 * f + 1] - A
            AC = P[3 * f + 2] - A
            normal = np.cross(AB, AC)
            normal = normal / np.linalg.norm(normal)
            for c in range(3):
                N[3 * f + c] = normal
        viz_mesh = Mesh(P, N)
        self.rendered_mesh = RenderedMesh(self.ctx, viz_mesh, self.program)

    def ensure_input_mesh(self):
        if self.input_mesh is not None:
            return
        mesh = OfxMeshInternal()
        mesh.point_count = len(self.mesh.P)
        mesh.corner_count = mesh.point_count
        mesh.face_count = mesh.point_count // 3
        mesh.allocate()
        # TODO: optimize this
        attr = mesh.attributes[kOfx.MeshAttribPoint][kOfx.MeshAttribPointPosition]
        attr.py_data[:] = [tuple(x for x in xyz) for xyz in self.mesh.P]

        attr = mesh.attributes[kOfx.MeshAttribCorner][kOfx.MeshAttribCornerPoint]
        attr.py_data[:] = np.arange(mesh.corner_count, dtype=int).tolist()

        attr = mesh.attributes[kOfx.MeshAttribFace][kOfx.MeshAttribFaceSize]
        attr.py_data[:] = (np.ones(mesh.face_count, dtype=int) * 3).tolist()

        self.input_mesh = mesh

def main():
    app = MyApp(1280, 720, "OpenMfx Playground - Elie Michel")
    app.main_loop()

if __name__ == "__main__":
    main()

