"""Run with Blender --background --factory-startup --python this_file.py."""

import importlib
import json
from pathlib import Path
import struct
import sys
import tempfile
import types

import bpy


package = types.ModuleType("game_rig_tools")
package.__path__ = [str(Path(__file__).resolve().parents[1])]
sys.modules[package.__name__] = package
bakery = importlib.import_module("game_rig_tools.GRT_Action_Bakery")
bakery.register()
package.glTF2ExportUserExtension = importlib.import_module(
    "game_rig_tools.GRT_Godot_Import"
).glTF2ExportUserExtension
bpy.context.preferences.addons.new().module = package.__name__


def create_rig(name):
    armature = bpy.data.armatures.new(name)
    rig = bpy.data.objects.new(name, armature)
    bpy.context.scene.collection.objects.link(rig)
    bpy.context.view_layer.objects.active = rig
    rig.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bone = armature.edit_bones.new("Bone")
    bone.tail = (0.0, 0.0, 1.0)
    bpy.ops.object.mode_set(mode="OBJECT")
    rig.select_set(False)
    return rig


control = create_rig("Control")
deform = create_rig("Deform")
constraint = deform.pose.bones["Bone"].constraints.new("COPY_LOCATION")
constraint.target = control
constraint.subtarget = "Bone"
constraint.owner_space = "POSE"
constraint.target_space = "POSE"
scene = bpy.context.scene
settings = scene.GRT_Action_Bakery_Global_Settings
settings.Source_Armature = control
settings.Target_Armature = deform
settings.GLOBAL_Baked_Name_Mode = "SUFFIX"
settings.GLOBAL_Baked_Name_01 = ".baked"
settings.Overwrite = True
settings.Bake_Popup = False
scene.frame_start = 1
scene.frame_end = 2

for name, distance in [("base", 1.0), ("woman", 3.0)]:
    action = bpy.data.actions.new(name)
    control.animation_data_create().action = action
    for frame, position in [(1, 0.0), (8, distance)]:
        control.pose.bones["Bone"].location.x = position
        control.pose.bones["Bone"].keyframe_insert("location", frame=frame)
    item = scene.GRT_Action_Bakery.add()
    item.Action = action
    item.Frame_Range_Mode = "ACTION"

assert bpy.ops.gamerigtool.bake_action_bakery() == {"FINISHED"}
track = deform.animation_data.nla_tracks[-1]
track.is_solo = True
constraint.mute = False
settings.Overwrite = False
assert bpy.ops.gamerigtool.bake_action_bakery() == {"FINISHED"}
with tempfile.TemporaryDirectory(prefix="game-rig-tools-bake-") as directory:
    filepath = str(Path(directory) / "baked.blend")
    bpy.ops.wm.save_as_mainfile(filepath=filepath)
    bpy.ops.wm.open_mainfile(filepath=filepath)

scene = bpy.context.scene
deform = bpy.data.objects["Deform"]
constraint = deform.pose.bones["Bone"].constraints[0]
assert constraint.mute, "A successful bake leaves the baked rig driven by its actions"
assert all(not track.is_solo for track in deform.animation_data.nla_tracks), "Every baked action is available for automatic import"
assert deform.animation_data.action is None, "Baked actions are stored in NLA tracks"
for name, distance in [("base", 1.0), ("woman", 3.0)]:
    action = bpy.data.actions[name + ".baked.001"]
    assert list(action.frame_range) == [1.0, 8.0], "The action range governs baking"
    deform.animation_data.use_nla = False
    deform.animation_data.action = action
    deform.animation_data.action_slot = action.slots[0]
    scene.frame_set(8)
    bpy.context.view_layer.update()
    assert abs(deform.pose.bones["Bone"].location.x - distance) < 0.0001, "Each baked action retains its own motion"

print("PASS: Bake Action Bakery prepares distinct full-range actions for automatic import")

# Save in the source-rig editing state, then exercise Blender's native glTF
# operator with the same output location and animation options used by Godot.
control = bpy.data.objects["Control"]
control.hide_viewport = False
control.select_set(True)
bpy.context.view_layer.objects.active = control
deform.hide_viewport = True
deform.select_set(False)
deform.animation_data.action = None
deform.animation_data.use_nla = True
deform.animation_data.nla_tracks[-1].is_solo = True
constraint.mute = False

with tempfile.TemporaryDirectory(prefix="game-rig-tools-import-") as directory:
    source = Path(directory) / "source.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(source))
    bpy.ops.wm.open_mainfile(filepath=str(source))
    saved_source = source.read_bytes()
    output = Path(directory) / ".godot" / "imported" / "source.gltf"
    output.parent.mkdir(parents=True)
    assert bpy.ops.export_scene.gltf(
        filepath=str(output),
        export_format="GLTF_SEPARATE",
        export_animations=True,
        export_animation_mode="ACTIONS",
        export_force_sampling=True,
        export_frame_range=False,
        use_visible=False,
        export_def_bones=False,
    ) == {"FINISHED"}

    document = json.loads(output.read_text())
    exported_rigs = {
        node["name"] for node in document["nodes"]
        if node.get("name") in {"Control", "Deform"}
    }
    assert exported_rigs == {"Deform"}, "Godot receives the configured game rig"
    assert {animation["name"] for animation in document["animations"]} == {
        "base.baked", "woman.baked", "base.baked.001", "woman.baked.001"
    }, "The game rig exports its assigned baked actions"
    buffers = [
        (output.parent / buffer["uri"]).read_bytes()
        for buffer in document["buffers"]
    ]
    deform_node = next(
        node for node in document["nodes"] if node.get("name") == "Deform"
    )
    bone_node = deform_node["children"][0]
    for name, distance in [("base", 1.0), ("woman", 3.0)]:
        animation = next(
            item for item in document["animations"]
            if item["name"] == name + ".baked.001"
        )
        channel = next(
            item for item in animation["channels"]
            if item["target"] == {"node": bone_node, "path": "translation"}
        )
        sampler = animation["samplers"][channel["sampler"]]
        accessor = document["accessors"][sampler["output"]]
        view = document["bufferViews"][accessor["bufferView"]]
        offset = view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
        stride = view.get("byteStride", 12)
        positions = [
            struct.unpack_from("<3f", buffers[view["buffer"]], offset + index * stride)[0]
            for index in range(accessor["count"])
        ]
        assert abs(max(positions) - distance) < 0.0001, "Godot receives each baked action's own motion"

    deform = bpy.data.objects["Deform"]
    assert bpy.data.objects["Control"].animation_data.action, "Source actions remain available for authoring"
    assert deform.hide_viewport, "The source-rig editing view is restored"
    assert not deform.pose.bones["Bone"].constraints[0].mute, "Source-rig control is restored"
    assert deform.animation_data.nla_tracks[-1].is_solo, "The editing track selection is restored"
    assert source.read_bytes() == saved_source, "Import preserves the manually saved Blender file"

    regular_output = Path(directory) / "regular.gltf"
    assert bpy.ops.export_scene.gltf(
        filepath=str(regular_output),
        export_format="GLTF_SEPARATE",
        export_animations=True,
        export_animation_mode="ACTIONS",
        export_force_sampling=True,
        export_frame_range=False,
        use_visible=False,
        export_def_bones=False,
    ) == {"FINISHED"}
    regular_document = json.loads(regular_output.read_text())
    regular_rigs = {
        node["name"] for node in regular_document["nodes"]
        if node.get("name") in {"Control", "Deform"}
    }
    assert regular_rigs == {"Control", "Deform"}, "Regular exports retain the authored rig selection"

print("PASS: Godot import uses baked motion with the source rig active")
