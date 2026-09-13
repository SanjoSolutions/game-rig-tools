"""Prepare baked rigs during Godot's built-in Blender import."""

from pathlib import Path

import bpy

from .GRT_Action_Bakery import get_all_rig_pairs, unique_objects


class BakedRigImportState:
    def __init__(self, rig):
        self.rig = rig
        self.hide_viewport = rig.hide_viewport
        self.constraints = [
            (constraint, constraint.mute)
            for bone in rig.pose.bones
            for constraint in bone.constraints
        ]
        self.tracks = [
            (track, track.is_solo) for track in rig.animation_data.nla_tracks
        ]

    def prepare(self):
        self.rig.hide_viewport = False
        for constraint, _ in self.constraints:
            constraint.mute = True
        for track, _ in self.tracks:
            track.is_solo = False

    def restore(self):
        self.rig.hide_viewport = self.hide_viewport
        for constraint, mute in self.constraints:
            constraint.mute = mute
        for track, is_solo in self.tracks:
            track.is_solo = is_solo


class glTF2ExportUserExtension:
    def __init__(self):
        self.rig_states = []
        self.source_rigs = []

    def pre_export_hook(self, export_settings):
        output_directory = Path(export_settings["gltf_filepath"]).parent
        if (
            bpy.app.background
            and output_directory.name == "imported"
            and output_directory.parent.name == ".godot"
            and export_settings["gltf_animations"]
        ):
            rig_pairs = get_all_rig_pairs(bpy.context)
            rigs = unique_objects([pair[1] for pair in rig_pairs])
            for rig in rigs:
                if rig.animation_data and any(
                    strip.action
                    for track in rig.animation_data.nla_tracks
                    for strip in track.strips
                ):
                    state = BakedRigImportState(rig)
                    self.rig_states.append(state)
                    state.prepare()
            prepared_rigs = [state.rig for state in self.rig_states]
            self.source_rigs = unique_objects([
                source for source, target in rig_pairs
                if target in prepared_rigs and source not in prepared_rigs
            ])
            if self.rig_states:
                # Each deform rig exports the actions assigned to its own slots.
                export_settings["gltf_export_anim_single_armature"] = False
            bpy.context.view_layer.update()

    def gather_tree_filter_tag_hook(self, tree, export_settings):
        # Godot aligns tracks across clips; source rigs stay in Blender for authoring.
        for node in tree.nodes.values():
            if node.blender_object in self.source_rigs:
                node.keep_tag = False

    def post_export_hook(self, export_settings):
        for state in self.rig_states:
            state.restore()
        self.rig_states.clear()
        self.source_rigs.clear()
        bpy.context.view_layer.update()
