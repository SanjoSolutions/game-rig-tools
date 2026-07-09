import bpy
from . import Utility
import os
from bpy_extras import anim_utils


script_file = os.path.realpath(__file__)
addon_directory = os.path.dirname(script_file)
addon_name = __package__


class GRT_Load_Action_Menu(bpy.types.Menu):
    bl_label = "Load Action Menu"
    bl_idname = "GRT_MT_load_action_menu"

    def draw(self, context):
        layout = self.layout

        Operator = layout.operator(
            "gamerigtool.action_bakery_list_operator",
            text="Load Action By Name",
            icon="SORTALPHA",
        )
        Operator.operation = "LOAD_ACTION_BY_NAME"

        Operator = layout.operator(
            "gamerigtool.action_bakery_list_operator",
            text="Load All Action",
            icon="IMPORT",
        )
        Operator.operation = "LOAD_ALL_ACTIONS"

        Operator = layout.operator(
            "gamerigtool.action_bakery_list_operator",
            text="Load From NLA",
            icon="NLA_PUSHDOWN",
        )
        Operator.operation = "LOAD_FROM_NLA"

        Operator = layout.operator(
            "gamerigtool.batch_rename_actions",
            text="Batch Rename Actions",
            icon="SORTALPHA",
        )


class GRT_OT_Toggle_Rig(bpy.types.Operator):
    """Toggle Rig"""

    bl_idname = "gamerigtool.toggle_rig"
    bl_label = "Toggle Rig"
    bl_options = {"UNDO", "REGISTER"}

    @classmethod
    def poll(cls, context):
        if len(get_all_rig_pairs(context)) > 0:
            return True

    def execute(self, context):
        scn = context.scene
        Global_Settings = scn.GRT_Action_Bakery_Global_Settings

        rig_pairs = get_all_rig_pairs(context)
        control_rigs = unique_objects([pair[0] for pair in rig_pairs])
        deform_rigs = unique_objects([pair[1] for pair in rig_pairs])
        first_control_rig = rig_pairs[0][0]
        show_control_rigs = first_control_rig.hide_viewport
        current_mode = context.object.mode if context.object else "OBJECT"

        first_control_rig.hide_set(False)
        first_control_rig.hide_viewport = False
        context.view_layer.objects.active = first_control_rig

        if context.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT", toggle=False)

        bpy.ops.object.select_all(action="DESELECT")

        for control_rig in control_rigs:
            control_rig.hide_set(False)
            control_rig.hide_viewport = False
        for deform_rig in deform_rigs:
            deform_rig.hide_set(False)
            deform_rig.hide_viewport = False

        if show_control_rigs:
            if Global_Settings.toggle_mute:
                bpy.ops.gamerigtool.toogle_game_rig_constraint(
                    mute=False, use_selected=False
                )

            for control_rig in control_rigs:
                control_rig.hide_viewport = False
                control_rig.select_set(True)
            for deform_rig in deform_rigs:
                deform_rig.hide_viewport = True

            context.view_layer.objects.active = control_rigs[0]

        else:
            if Global_Settings.toggle_mute:
                bpy.ops.gamerigtool.toogle_game_rig_constraint(
                    mute=True, use_selected=False
                )

            for control_rig in control_rigs:
                control_rig.hide_viewport = True
            for deform_rig in deform_rigs:
                deform_rig.hide_viewport = False
                deform_rig.select_set(True)

            context.view_layer.objects.active = deform_rigs[0]

        if current_mode == "POSE":
            try:
                bpy.ops.object.mode_set(mode="POSE", toggle=False)
            except RuntimeError:
                pass
        if current_mode == "EDIT":
            try:
                bpy.ops.object.mode_set(mode="EDIT", toggle=False)
            except RuntimeError:
                pass

        #

        Utility.update_UI()

        return {"FINISHED"}


class GRT_Action_Bakery_Set_Frame_Range_To_Action(bpy.types.Operator):
    """Set Frame Range to Action"""

    bl_idname = "gamerigtool.action_bakery_set_frame_range_to_action"
    bl_label = "Set Frame Range To Action"
    bl_options = {"UNDO", "REGISTER"}

    index: bpy.props.IntProperty()

    def execute(self, context):
        scn = context.scene
        item_list = scn.GRT_Action_Bakery
        item_index = self.index

        active_baker = item_list[item_index]

        if active_baker.Action:
            active_baker.Set_FR_Start = int(active_baker.Action.frame_range[0])
            active_baker.Set_FR_End = int(active_baker.Action.frame_range[1])

        Utility.update_UI()

        return {"FINISHED"}


ENUM_list_operation = [
    ("ADD", "Add", "Add"),
    ("REMOVE", "Remove", "Remove"),
    ("UP", "Up", "Up"),
    ("DOWN", "Down", "Down"),
    ("ASSIGN", "Assign", "Assign"),
    ("UNASSIGN", "Unassign", "Unassign"),
    ("LOAD_ALL_ACTIONS", "Load All Actions", "Load All Actions"),
    ("LOAD_ACTIVE_ACTIONS", "Load Active Actions", "Load Active Actions"),
    ("LOAD_ACTION_BY_NAME", "Load Action By Name", "Load Action By Name"),
    ("LOAD_FROM_NLA", "Load From NLA", "Load From NLA"),
    ("CLEAR_ALL_ACTIONS", "Clear All Action", "Clear All Action"),
]


ENUM_rig_pair_operation = [
    ("ADD", "Add", "Add"),
    ("REMOVE", "Remove", "Remove"),
    ("UP", "Up", "Up"),
    ("DOWN", "Down", "Down"),
]


class GRT_Action_Bakery_Rig_Pair_List_Operator(bpy.types.Operator):
    """Rig Pair List Operator"""

    bl_idname = "gamerigtool.action_bakery_rig_pair_list_operator"
    bl_label = "Rig Pair List Operator"
    bl_options = {"UNDO", "REGISTER"}

    operation: bpy.props.EnumProperty(items=ENUM_rig_pair_operation)
    index: bpy.props.IntProperty()

    def execute(self, context):
        scn = context.scene
        settings = scn.GRT_Action_Bakery_Global_Settings
        item_list = scn.GRT_Action_Bakery_Rig_Pairs
        item_index = self.index

        if self.operation == "ADD":
            item = item_list.add()
            if context.object and context.object.type == "ARMATURE":
                item.Source_Armature = context.object
            else:
                item.Source_Armature = settings.Source_Armature
            item.Target_Armature = settings.Target_Armature
            scn.GRT_Action_Bakery_Rig_Pair_Index = len(item_list) - 1
            Utility.update_UI()
            return {"FINISHED"}

        if self.operation == "REMOVE":
            if len(item_list) > 0 and 0 <= item_index < len(item_list):
                item_list.remove(item_index)
                if len(item_list) == scn.GRT_Action_Bakery_Rig_Pair_Index:
                    scn.GRT_Action_Bakery_Rig_Pair_Index = len(item_list) - 1
                Utility.update_UI()
            return {"FINISHED"}

        if self.operation == "UP":
            if item_index >= 1:
                item_list.move(item_index, item_index - 1)
                scn.GRT_Action_Bakery_Rig_Pair_Index -= 1
            return {"FINISHED"}

        if self.operation == "DOWN":
            if len(item_list) - 1 > item_index:
                item_list.move(item_index, item_index + 1)
                scn.GRT_Action_Bakery_Rig_Pair_Index += 1
            return {"FINISHED"}

        Utility.update_UI()
        return {"FINISHED"}


class GRT_Action_Bakery_List_Operator(bpy.types.Operator):
    """List Operator"""

    bl_idname = "gamerigtool.action_bakery_list_operator"
    bl_label = "List Operator"
    bl_options = {"UNDO", "REGISTER"}

    operation: bpy.props.EnumProperty(items=ENUM_list_operation)
    action: bpy.props.StringProperty()
    index: bpy.props.IntProperty()

    assign: bpy.props.BoolProperty(default=True)
    name_include: bpy.props.StringProperty()

    def draw(self, context):
        if self.operation == "ADD":
            layout = self.layout
            layout.prop_search(self, "action", bpy.data, "actions", text="Action")
        if self.operation == "LOAD_ACTION_BY_NAME":
            layout = self.layout
            layout.prop(self, "name_include", text="Name Include")

    def invoke(self, context, event):
        if self.operation in ["ADD", "LOAD_ACTION_BY_NAME"]:
            return context.window_manager.invoke_props_dialog(self)
        else:
            return self.execute(context)

    def execute(self, context):
        scn = context.scene
        item_list = scn.GRT_Action_Bakery
        item_index = self.index

        # if len(item_list) > 0:
        #
        #     for item in item_list:
        #         for index, action in enumerate(item_list):
        #             if not item.Action:
        #                 item_list.remove(index)
        #                 break

        if self.operation == "CLEAR_ALL_ACTIONS":
            item_list.clear()

            return {"FINISHED"}

        if self.operation == "LOAD_FROM_NLA":
            object = context.object
            if object:
                if object.type == "ARMATURE":
                    if object.animation_data:
                        for nla_track in object.animation_data.nla_tracks:
                            for nla_strip in nla_track.strips:
                                action = nla_strip.action

                                if action:
                                    check = [item.Action for item in item_list]

                                    if action not in check:
                                        item = item_list.add()
                                        item.Action = action
                                        item.LOCAL_Baked_Name = "BAKED_" + action.name

                                        item.Set_FR_Start = int(action.frame_range[0])
                                        item.Set_FR_End = int(action.frame_range[1])

                                        scn.GRT_Action_Bakery_Index = len(item_list) - 1

            Utility.update_UI()

            return {"FINISHED"}

        if self.operation == "LOAD_ACTION_BY_NAME":
            for action in bpy.data.actions:
                check = [item.Action for item in item_list]

                if action not in check:
                    if self.name_include in action.name:
                        item = item_list.add()
                        item.Action = action
                        item.LOCAL_Baked_Name = "BAKED_" + action.name

                        item.Set_FR_Start = int(action.frame_range[0])
                        item.Set_FR_End = int(action.frame_range[1])

                        scn.GRT_Action_Bakery_Index = len(item_list) - 1

            Utility.update_UI()

            return {"FINISHED"}

        if self.operation == "LOAD_ACTIVE_ACTIONS":
            object = context.object
            if object:
                if object.type == "ARMATURE":
                    action = None

                    if object.animation_data:
                        if object.animation_data.action:
                            action = object.animation_data.action

                    if action:
                        check = [item.Action for item in item_list]

                        if action not in check:
                            item = item_list.add()
                            item.Action = action
                            item.LOCAL_Baked_Name = "BAKED_" + action.name

                            item.Set_FR_Start = int(action.frame_range[0])
                            item.Set_FR_End = int(action.frame_range[1])

                            scn.GRT_Action_Bakery_Index = len(item_list) - 1

            Utility.update_UI()

            return {"FINISHED"}

        if self.operation == "LOAD_ALL_ACTIONS":
            for action in bpy.data.actions:
                check = [item.Action for item in item_list]

                if action not in check:
                    item = item_list.add()
                    item.Action = action
                    item.LOCAL_Baked_Name = "BAKED_" + action.name

                    item.Set_FR_Start = int(action.frame_range[0])
                    item.Set_FR_End = int(action.frame_range[1])

                    scn.GRT_Action_Bakery_Index = len(item_list) - 1

            Utility.update_UI()

            return {"FINISHED"}

        if self.operation == "REMOVE":
            item_list.remove(self.index)

            if len(item_list) == scn.GRT_Action_Bakery_Index:
                scn.GRT_Action_Bakery_Index = len(item_list) - 1
            Utility.update_UI()
            return {"FINISHED"}

        if self.operation == "ADD":
            Action = bpy.data.actions.get(self.action)

            if Action:
                item = item_list.add()
                item.Action = Action

                item.LOCAL_Baked_Name = "BAKED_" + Action.name

                scn.GRT_Action_Bakery_Index = len(item_list) - 1

                Utility.update_UI()

            return {"FINISHED"}

        if self.operation == "UP":
            if item_index >= 1:
                item_list.move(item_index, item_index - 1)
                scn.GRT_Action_Bakery_Index -= 1
                return {"FINISHED"}

        if self.operation == "DOWN":
            if len(item_list) - 1 > item_index:
                item_list.move(item_index, item_index + 1)
                scn.GRT_Action_Bakery_Index += 1
                return {"FINISHED"}

        Utility.update_UI()
        return {"FINISHED"}


class GRT_UL_Action_Bakery_List(bpy.types.UIList):
    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):
        scn = context.scene
        ob = data
        row = layout.row(align=True)

        Action = item.Action

        if Action:
            row.prop(item, "Bake_Select", text="")
            # row.prop(item, "Action", text="", emboss=False)
            row.prop(Action, "name", text="", emboss=False, icon="ACTION")
        else:
            row.label(text="Missing Action", icon="ERROR")

        # row = row.row(align=True)
        # row.alignment = "RIGHT"
        # row.prop(item, "use_loop", text="", icon="FILE_REFRESH")

        Operator = row.operator(
            "gamerigtool.action_bakery_list_operator", text="", icon="X"
        )
        Operator.operation = "REMOVE"
        Operator.index = index

        # row.prop(Action, "name", text="")


class GRT_UL_Action_Bakery_Rig_Pair_List(bpy.types.UIList):
    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):
        row = layout.row(align=True)
        row.prop(item, "enabled", text="")

        if item.Source_Armature:
            row.label(text=item.Source_Armature.name, icon="OUTLINER_OB_ARMATURE")
        else:
            row.label(text="Missing Control Rig", icon="ERROR")

        row.label(text="", icon="FORWARD")

        if item.Target_Armature:
            row.label(text=item.Target_Armature.name, icon="OUTLINER_OB_ARMATURE")
        else:
            row.label(text="Missing Game Rig", icon="ERROR")

        Operator = row.operator(
            "gamerigtool.action_bakery_rig_pair_list_operator", text="", icon="X"
        )
        Operator.operation = "REMOVE"
        Operator.index = index


class GRT_PT_Action_Bakery(bpy.types.Panel):
    bl_label = "Game Rig Tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Game Rig Tools"

    # @classmethod
    # def poll(cls, context):

    # Top Bar Toogle Constraint Update

    # addon_preferences = context.preferences.addons[addon_name].preferences
    #
    # if addon_preferences.side_panel:
    #     return True
    # else:
    #     return False

    def draw(self, context):
        layout = self.layout

        scn = context.scene

        addon_preferences = context.preferences.addons[addon_name].preferences

        row = layout.row(align=True)

        # operator = row.operator(
        #     "gamerigtool.toogle_game_rig_constraint", text="Mute", icon="HIDE_ON"
        # )
        # operator.mute = True
        # operator.use_selected = addon_preferences.use_selected
        #
        # operator = row.operator(
        #     "gamerigtool.toogle_game_rig_constraint", text="Unmute", icon="HIDE_OFF"
        # )
        # operator.mute = False
        # operator.use_selected = addon_preferences.use_selected
        #
        # row.prop(addon_preferences, "use_selected", text="", icon="RESTRICT_SELECT_OFF")
        #

        Global_Settings = scn.GRT_Action_Bakery_Global_Settings

        row = layout.row(align=True)

        active_pair = get_selected_rig_pair(context)
        control_rig, deform_rig = get_selected_rig_pair_objects(context)

        constraint_state = []

        target_rigs = unique_objects([pair[1] for pair in get_all_rig_pairs(context)])

        for target_rig in target_rigs:
            for bone in target_rig.pose.bones:
                for constraint in bone.constraints:
                    constraint_state.append(not constraint.mute)

        if len(constraint_state) > 0:
            if all(constraint_state):
                operator = row.operator(
                    "gamerigtool.toogle_game_rig_constraint",
                    text="Connected",
                    icon="LINKED",
                    depress=True,
                )
                operator.mute = True
                # operator.use_selected = addon_preferences.use_selected
                operator.use_selected = False
                # row.prop(
                #     Global_Settings, "Connection", text="Connect", icon="CONSTRAINT_BONE"
                # )
            else:
                operator = row.operator(
                    "gamerigtool.toogle_game_rig_constraint",
                    text="Disconnected",
                    icon="UNLINKED",
                    depress=False,
                )
                operator.mute = False
                # operator.use_selected = addon_preferences.use_selected
                operator.use_selected = False

                if any(constraint_state):
                    row = layout.row(align=True)
                    row.label(text="Partial Connection", icon="INFO")
                # row.prop(
                #     Global_Settings, "Connection", text="Disconnect", icon="CONSTRAINT_BONE"
                # )
        else:
            row.label(text="No Constraint / Connection", icon="INFO")

        row = layout.row(align=True)
        row.operator("gamerigtool.toggle_rig", text="Toggle Rig")
        row.prop(Global_Settings, "toggle_mute", text="", icon="CONSTRAINT_BONE")
        # layout.label(text="Bake Settings")

        col = layout.column(align=True)
        col.label(text="Rig Pairs")
        row = col.row(align=True)
        col2 = row.column(align=True)
        col2.template_list(
            "GRT_UL_Action_Bakery_Rig_Pair_List",
            "",
            scn,
            "GRT_Action_Bakery_Rig_Pairs",
            scn,
            "GRT_Action_Bakery_Rig_Pair_Index",
            rows=2,
        )

        col3 = row.column(align=True)
        Operator = col3.operator(
            "gamerigtool.action_bakery_rig_pair_list_operator", text="", icon="ADD"
        )
        Operator.operation = "ADD"
        Operator.index = scn.GRT_Action_Bakery_Rig_Pair_Index

        Operator = col3.operator(
            "gamerigtool.action_bakery_rig_pair_list_operator", text="", icon="REMOVE"
        )
        Operator.operation = "REMOVE"
        Operator.index = scn.GRT_Action_Bakery_Rig_Pair_Index

        col3.separator()

        Operator = col3.operator(
            "gamerigtool.action_bakery_rig_pair_list_operator", text="", icon="TRIA_UP"
        )
        Operator.operation = "UP"
        Operator.index = scn.GRT_Action_Bakery_Rig_Pair_Index

        Operator = col3.operator(
            "gamerigtool.action_bakery_rig_pair_list_operator",
            text="",
            icon="TRIA_DOWN",
        )
        Operator.operation = "DOWN"
        Operator.index = scn.GRT_Action_Bakery_Rig_Pair_Index

        if len(scn.GRT_Action_Bakery_Rig_Pairs) > 0:
            if scn.GRT_Action_Bakery_Rig_Pair_Index < len(
                scn.GRT_Action_Bakery_Rig_Pairs
            ):
                active_pair = scn.GRT_Action_Bakery_Rig_Pairs[
                    scn.GRT_Action_Bakery_Rig_Pair_Index
                ]
                col.label(text="Control Rig")
                row = col.row(align=True)
                row.prop(active_pair, "Source_Armature", text="")
                if active_pair.Source_Armature:
                    row.prop(active_pair.Source_Armature, "hide_viewport", text="")

                col.label(text="Game Rig")
                row = col.row(align=True)
                row.prop(active_pair, "Target_Armature", text="")
                if active_pair.Target_Armature:
                    row.prop(active_pair.Target_Armature, "hide_viewport", text="")
        else:
            col.label(text="Add a rig pair to choose control and game rigs", icon="INFO")

        layout.separator()

        col = layout.column(align=True)
        col.scale_y = 2

        if not control_rig:
            col.enabled = False

        if not deform_rig:
            op = col.operator(
                "gamerigtool.generate_game_rig",
                text="Generate Game Rig",
                icon="OUTLINER_OB_ARMATURE",
            )
            op.Use_Regenerate_Rig = False
            op.Use_Legacy = False
        else:
            op = col.operator(
                "gamerigtool.generate_game_rig",
                text="Regenerate Game Rig",
                icon="FILE_REFRESH",
            )
            op.Use_Regenerate_Rig = True
            op.Use_Legacy = False


        layout.prop(Global_Settings, "use_post_generation_script" ,text="Post Generation Script")
        if Global_Settings.use_post_generation_script:
            layout.prop(Global_Settings, "post_generation_script" ,text="")


        if not control_rig:
            box = layout.box()
            box.label(text="Select Control Rig", icon="INFO")

        # op = layout.operator("gamerigtool.generate_game_rig", text="Generate Game Rig (Legacy)", icon="OUTLINER_OB_ARMATURE")
        # op.Use_Regenerate_Rig = False
        # op.Use_Legacy = True

        subheader, subpanel = layout.panel("grt_utility_tool", default_closed=False)
        subheader.label(text="Action Bakery", icon="ACTION")
        if subpanel:
            # if Utility.draw_subpanel(
            #     Global_Settings,
            #     Global_Settings.Show_Action_Bakery,
            #     "Show_Action_Bakery",
            #     "Action Bakery",
            #     layout,
            # ):

            row = subpanel.row(align=True)
            col2 = row.column(align=True)
            col2.template_list(
                "GRT_UL_Action_Bakery_List",
                "",
                scn,
                "GRT_Action_Bakery",
                scn,
                "GRT_Action_Bakery_Index",
            )

            col = row.column(align=True)

            Operator = col.operator(
                "gamerigtool.action_bakery_list_operator", text="", icon="ADD"
            )
            Operator.operation = "ADD"
            Operator.index = scn.GRT_Action_Bakery_Index

            Operator = col.operator(
                "gamerigtool.action_bakery_list_operator", text="", icon="REMOVE"
            )
            Operator.operation = "REMOVE"
            Operator.index = scn.GRT_Action_Bakery_Index

            col.separator()
            col.menu("GRT_MT_load_action_menu", text="", icon="DOWNARROW_HLT")
            col.separator()

            Operator = col.operator(
                "gamerigtool.action_bakery_list_operator", text="", icon="TRIA_UP"
            )
            Operator.operation = "UP"
            Operator.index = scn.GRT_Action_Bakery_Index

            Operator = col.operator(
                "gamerigtool.action_bakery_list_operator", text="", icon="TRIA_DOWN"
            )
            Operator.operation = "DOWN"
            Operator.index = scn.GRT_Action_Bakery_Index

            # Operator = col.operator("gamerigtool.action_bakery_list_operator", text="", icon="SORTALPHA")
            # Operator.operation = "LOAD_ACTION_BY_NAME"
            #
            #
            #

            # Operator = row2.operator("gamerigtool.action_bakery_list_operator", text="All Action", icon="IMPORT")
            # Operator.operation = "LOAD_ALL_ACTIONS"
            LOAD_ACTION_ENABLE = False
            LOAD_NLA_ENABLE = False
            object = context.object
            if object:
                if object.type == "ARMATURE":
                    if object.animation_data:
                        if object.animation_data.action:
                            LOAD_ACTION_ENABLE = True

            if object:
                if object.type == "ARMATURE":
                    if object.animation_data:
                        LOAD_NLA_ENABLE = True

            row2 = col2.row(align=True)

            row3 = row2.row(align=True)
            row3.enabled = True
            row3.enabled = LOAD_ACTION_ENABLE
            Operator = row3.operator(
                "gamerigtool.action_bakery_list_operator", text="Active", icon="IMPORT"
            )
            Operator.operation = "LOAD_ACTIVE_ACTIONS"

            row3 = row2.row(align=True)
            row3.enabled = LOAD_NLA_ENABLE

            Operator = row3.operator(
                "gamerigtool.action_bakery_list_operator",
                text="From NLA",
                icon="NLA_PUSHDOWN",
            )
            Operator.operation = "LOAD_FROM_NLA"

            row2 = col2.row(align=True)

            Operator = row2.operator(
                "gamerigtool.action_bakery_list_operator",
                text="Load All",
                icon="IMPORT",
            )
            Operator.operation = "LOAD_ALL_ACTIONS"

            Operator = row2.operator(
                "gamerigtool.action_bakery_list_operator",
                text="Clear All",
                icon="TRASH",
            )
            Operator.operation = "CLEAR_ALL_ACTIONS"

            if len(scn.GRT_Action_Bakery) > 0:
                if scn.GRT_Action_Bakery_Index < len(scn.GRT_Action_Bakery):
                    active_baker = context.scene.GRT_Action_Bakery[
                        scn.GRT_Action_Bakery_Index
                    ]

                    col2.prop(active_baker, "Action", text="")

                    # layout.separator()
                    #
                    # col = layout.column(align=True)
                    # col.label(text="Control Rig")
                    # col.prop(Global_Settings, "Source_Armature", text="")
                    # col.label(text="Game Rig")
                    # col.prop(Global_Settings, "Target_Armature", text="")
                    # col.prop(Global_Settings, "Bake_Popup", text="Use Operator Popup")

                    # if Utility.draw_subpanel(active_baker, active_baker.SHOW_Local_Settings, "SHOW_Local_Settings", "Local Settings", layout):

                    subpanel.label(text="Local Settings")

                    col3 = subpanel.column(align=True)
                    col3.prop(
                        active_baker, "use_Local_Name", text="Set Baked Action name"
                    )

                    if active_baker.use_Local_Name:
                        col3.prop(active_baker, "LOCAL_Baked_Name", text="")

                    # row3 = col3.row(align=True)
                    # row3.prop(active_baker, "use_loop", text="Loop", icon="FILE_REFRESH")

                    #
                    # if not active_baker.use_loop:
                    #

                    if active_baker.Action:
                        col3.separator()
                        col3.label(text="Frame Range")
                        row3 = col3.row(align=True)
                        row3.prop(active_baker, "Frame_Range_Mode", expand=True)

                        if active_baker.Frame_Range_Mode == "ACTION":
                            row3 = col3.row(align=True)
                            # row3.prop(active_baker.Action, "frame_range", text="")
                            row3.label(
                                text="Start: "
                                + str(active_baker.Action.frame_range[0]),
                                icon="ACTION",
                            )
                            row3.label(
                                text="End: " + str(active_baker.Action.frame_range[1]),
                                icon="ACTION",
                            )
                            col3.separator()

                        if active_baker.Frame_Range_Mode == "SET":
                            row3 = col3.row(align=True)
                            row3.prop(active_baker, "Set_FR_Start", text="Set Start")
                            row3.prop(active_baker, "Set_FR_End", text="Set End")
                            row3.operator(
                                "gamerigtool.action_bakery_set_frame_range_to_action",
                                text="",
                                icon="FILE_REFRESH",
                            ).index = scn.GRT_Action_Bakery_Index
                            col3.separator()

                        if active_baker.Frame_Range_Mode == "TRIM":
                            row3 = col3.row(align=True)
                            row3.prop(active_baker, "Trim_FR_Start", text="Trim Start")
                            row3.prop(active_baker, "Trim_FR_End", text="Trim End")

                            row3 = col3.row(align=True)
                            row3.label(
                                text="Start: "
                                + str(
                                    active_baker.Action.frame_range[0]
                                    + active_baker.Trim_FR_Start
                                ),
                                icon="SCULPTMODE_HLT",
                            )
                            row3.label(
                                text="End: "
                                + str(
                                    active_baker.Action.frame_range[1]
                                    - active_baker.Trim_FR_End
                                ),
                                icon="SCULPTMODE_HLT",
                            )
                            col3.separator()

                        col3.prop(
                            active_baker,
                            "offset_keyframe_to_frame_one",
                            text="Offset to Frame One",
                        )
                    # if active_baker.use_Local_Trim:
                    #
                    #     col3.prop(active_baker, "LOCAL_Trim", text="Trim")

            # box.label(text="Baked Name: " + Change_to_Baked_Name(context, item))

            if len(get_rig_pairs(context)) == 0 and not Global_Settings.Source_Armature:
                box = subpanel.box()
                box.label(text="Select Control Rig", icon="ERROR")
            if len(get_rig_pairs(context)) == 0 and not Global_Settings.Target_Armature:
                box = subpanel.box()
                box.label(text="Select Game Rig", icon="ERROR")

            for pair in scn.GRT_Action_Bakery_Rig_Pairs:
                if pair.enabled and (not pair.Source_Armature or not pair.Target_Armature):
                    box = subpanel.box()
                    box.label(text="Enabled rig pair is incomplete", icon="ERROR")
                    break

            for item in check_invalid_name(context):
                box = subpanel.box()
                box.label(text=item.Action.name, icon="ERROR")
                box.label(text="Baked Action Have Same Action Name")
                box.label(text="Possible Solutions:", icon="INFO")
                box.label(text="A: Adjust Baked Name Settings")
                box.label(text="B: Turn Off Overwrite")

            row = subpanel.row(align=True)

            col = row.column(align=True)
            col.scale_y = 2
            row2 = col.row(align=True)
            row2.operator("gamerigtool.bake_action_bakery", icon="KEYTYPE_KEYFRAME_VEC")
            row2.prop(Global_Settings, "Bake_Popup", text="", icon="SETTINGS")

            subpanel.prop(Global_Settings, "Overwrite", text="Overwrite")

            subpanel.prop(Global_Settings, "Push_to_NLA", text="Push To NLA")

            subpanel.separator()

            subheader, subpanel = subpanel.panel(
                "grt_bake_settings", default_closed=False
            )
            subheader.label(text="Global Bake Settings", icon="SETTINGS")
            if subpanel:
                # if Utility.draw_subpanel(
                #     Global_Settings,
                #     Global_Settings.SHOW_Bake_Settings,
                #     "SHOW_Bake_Settings",
                #     "Global Bake Settings",
                #     subpanel,
                # ):

                draw_global_bake_settings(subpanel, context)


def draw_global_bake_settings(layout, context):
    scn = context.scene
    Global_Settings = scn.GRT_Action_Bakery_Global_Settings

    col = layout.column(align=True)

    col.label(text="Baked Name")

    row = col.row(align=True)
    row.prop(Global_Settings, "GLOBAL_Baked_Name_Mode", expand=True)

    if Global_Settings.GLOBAL_Baked_Name_Mode == "SUFFIX":
        col.prop(Global_Settings, "GLOBAL_Baked_Name_01", text="Suffix")

    if Global_Settings.GLOBAL_Baked_Name_Mode == "PREFIX":
        col.prop(Global_Settings, "GLOBAL_Baked_Name_01", text="Prefix")

    if Global_Settings.GLOBAL_Baked_Name_Mode == "REPLACE":
        col.prop(Global_Settings, "GLOBAL_Baked_Name_01", text="From")
        col.prop(Global_Settings, "GLOBAL_Baked_Name_02", text="To")

    # layout.separator()
    #
    # layout.label(text="Trim End")
    # row = layout.row(align=True)
    # row.prop(Global_Settings, "GLOBAL_Trim_End_Frame", text="")

    layout.separator()

    layout.label(text="Settings")
    layout.operator(
        "gamerigtool.reset_bake_settings_to_default",
        text="Reset To Default",
        icon="FILE_REFRESH",
    )
    layout.prop(
        Global_Settings, "Pre_Unmute_Constraint", text="Unmute Constraints Before Bake"
    )
    layout.prop(
        Global_Settings, "Post_Mute_Constraint", text="Mute Constraints After Bake"
    )
    layout.prop(
        Global_Settings,
        "GLOBAL_Clear_Transform_Before_Bake",
        text="Clear Transform Before Baking",
    )

    layout.separator()

    layout.label(text="Bake Settings")
    layout.prop(Global_Settings, "BAKE_SETTINGS_Only_Selected", text="Only Selected")
    layout.prop(Global_Settings, "BAKE_SETTINGS_Do_Visual_Keying", text="Visual Keying")
    layout.prop(
        Global_Settings, "BAKE_SETTINGS_Do_Constraint_Clear", text="Clear Constraint"
    )
    layout.prop(Global_Settings, "BAKE_SETTINGS_Do_Parent_Clear", text="Clear Parent")
    layout.prop(Global_Settings, "BAKE_SETTINGS_Do_Clean", text="Clean Curves")
    layout.prop(Global_Settings, "BAKE_SETTINGS_Do_Pose", text="Bake Pose")
    layout.prop(Global_Settings, "BAKE_SETTINGS_Do_Object", text="Bake Object")

    layout.label(text="Channels")
    layout.prop(Global_Settings, "BAKE_SETTINGS_Location", text="Location")
    layout.prop(Global_Settings, "BAKE_SETTINGS_Rotation", text="Rotaton")
    layout.prop(Global_Settings, "BAKE_SETTINGS_Scale", text="Scale")
    layout.prop(Global_Settings, "BAKE_SETTINGS_BBone", text="BBone")
    layout.prop(
        Global_Settings, "BAKE_SETTINGS_Custom_Properties", text="Custom Properties"
    )


def POLL_Deform_Armature(self, object):
    if object != self.Source_Armature:
        if object in list(bpy.context.scene.objects):
            return object.type == "ARMATURE"


def POLL_Control_Armature(self, object):
    if object != self.Target_Armature:
        if object in list(bpy.context.scene.objects):
            return object.type == "ARMATURE"


def UPDATE_SET_Start(self, context):
    if self.Set_FR_Start >= self.Set_FR_End:
        self.Set_FR_End = self.Set_FR_Start + 1


def UPDATE_SET_End(self, context):
    if self.Set_FR_End <= self.Set_FR_Start:
        self.Set_FR_Start = self.Set_FR_End - 1


# Set to Action


def UPDATE_TRIM_Start(self, context):
    if self.Action:
        start = int(self.Action.frame_range[0]) + self.Trim_FR_Start
        end = int(self.Action.frame_range[1]) - self.Trim_FR_End

        if start >= end:
            self.Trim_FR_Start = end - 2


def UPDATE_TRIM_End(self, context):
    if self.Action:
        start = int(self.Action.frame_range[0]) + self.Trim_FR_Start
        end = int(self.Action.frame_range[1]) - self.Trim_FR_End

        if end <= start:
            self.Trim_FR_End = (
                int(self.Action.frame_range[1])
                - int(self.Action.frame_range[0])
                + self.Trim_FR_Start
                - 1
            )


ENUM_Trim_Type = [
    ("KEYFRAME", "Keyframe", "Keyframe"),
    ("NLA_STRIP", "NLA Strip", "NLA Strip"),
]
ENUM_Frame_Range_Mode = [
    ("ACTION", "Action", "Action"),
    ("SET", "Set", "Set"),
    ("TRIM", "Trim", "Trim"),
]


class GRT_Action_Bakery_Property_Group(bpy.types.PropertyGroup):
    Action: bpy.props.PointerProperty(name="Action", type=bpy.types.Action)
    Bake_Select: bpy.props.BoolProperty(default=True)

    SHOW_Local_Settings: bpy.props.BoolProperty(default=False)

    use_Local_Name: bpy.props.BoolProperty()
    LOCAL_Baked_Name: bpy.props.StringProperty()

    use_Local_Trim: bpy.props.BoolProperty()

    Frame_Range_Mode: bpy.props.EnumProperty(items=ENUM_Frame_Range_Mode)
    Set_FR_Start: bpy.props.IntProperty(min=0, update=UPDATE_SET_Start)
    Set_FR_End: bpy.props.IntProperty(min=1, default=1, update=UPDATE_SET_End)

    Trim_FR_Start: bpy.props.IntProperty(min=0, update=UPDATE_TRIM_Start)
    Trim_FR_End: bpy.props.IntProperty(min=0, update=UPDATE_TRIM_End)

    offset_keyframe_to_frame_one: bpy.props.BoolProperty(default=False)

    # use_loop: bpy.props.BoolProperty()
    LOCAL_Trim: bpy.props.IntProperty(min=0)


class GRT_Action_Bakery_Rig_Pair_Property_Group(bpy.types.PropertyGroup):
    enabled: bpy.props.BoolProperty(default=True)
    Source_Armature: bpy.props.PointerProperty(
        name="Control Armature", type=bpy.types.Object, poll=POLL_Control_Armature
    )
    Target_Armature: bpy.props.PointerProperty(
        name="Game Armature", type=bpy.types.Object, poll=POLL_Deform_Armature
    )


def UPDATE_active_to_control_rig(self, context):
    if context.object:
        if context.object.type == "ARMATURE":
            if not context.object == self.Target_Armature:
                self.Source_Armature = context.object

    if self.active_to_control_rig:
        self.active_to_control_rig = False


def UPDATE_active_to_game_rig(self, context):
    if context.object:
        if context.object.type == "ARMATURE":
            if not context.object == self.Source_Armature:
                self.Target_Armature = context.object

    if self.active_to_game_rig:
        self.active_to_game_rig = False


ENUM_Baked_Name_Mode = [
    ("SUFFIX", "Suffix", "Suffix"),
    ("PREFIX", "Prefix", "Prefix"),
    ("REPLACE", "Replace", "Replace"),
]


class GRT_Action_Bakery_Global_Settings_Property_Group(bpy.types.PropertyGroup):
    Push_to_NLA: bpy.props.BoolProperty(default=True)
    Pre_Unmute_Constraint: bpy.props.BoolProperty(default=True)
    Post_Mute_Constraint: bpy.props.BoolProperty(default=True)

    toggle_mute: bpy.props.BoolProperty(default=True)

    GLOBAL_Baked_Name_Mode: bpy.props.EnumProperty(items=ENUM_Baked_Name_Mode)
    GLOBAL_Baked_Name_01: bpy.props.StringProperty()
    GLOBAL_Baked_Name_02: bpy.props.StringProperty()

    Overwrite: bpy.props.BoolProperty()
    Clean_Empty_NLA_Strip: bpy.props.BoolProperty(default=True)

    GLOBAL_Trim_End_Frame: bpy.props.IntProperty(min=0)

    SHOW_Bake_Settings: bpy.props.BoolProperty(default=False)

    Source_Armature: bpy.props.PointerProperty(
        name="Control Armature", type=bpy.types.Object, poll=POLL_Control_Armature
    )
    Target_Armature: bpy.props.PointerProperty(
        name="Deform Armature", type=bpy.types.Object, poll=POLL_Deform_Armature
    )

    Bake_Popup: bpy.props.BoolProperty(default=True)

    BAKE_SETTINGS_Only_Selected: bpy.props.BoolProperty(default=False)
    BAKE_SETTINGS_Do_Pose: bpy.props.BoolProperty(default=True)
    BAKE_SETTINGS_Do_Object: bpy.props.BoolProperty(default=False)
    BAKE_SETTINGS_Do_Visual_Keying: bpy.props.BoolProperty(default=True)
    BAKE_SETTINGS_Do_Constraint_Clear: bpy.props.BoolProperty(default=False)
    BAKE_SETTINGS_Do_Parent_Clear: bpy.props.BoolProperty(default=False)
    BAKE_SETTINGS_Do_Clean: bpy.props.BoolProperty(default=False)

    BAKE_SETTINGS_Location: bpy.props.BoolProperty(default=True)
    BAKE_SETTINGS_Rotation: bpy.props.BoolProperty(default=True)
    BAKE_SETTINGS_Scale: bpy.props.BoolProperty(default=True)
    BAKE_SETTINGS_BBone: bpy.props.BoolProperty(default=True)
    BAKE_SETTINGS_Custom_Properties: bpy.props.BoolProperty(default=True)

    active_to_control_rig: bpy.props.BoolProperty(
        default=False, update=UPDATE_active_to_control_rig
    )
    active_to_game_rig: bpy.props.BoolProperty(
        default=False, update=UPDATE_active_to_game_rig
    )

    Show_Action_Bakery: bpy.props.BoolProperty(default=False)

    GLOBAL_Clear_Transform_Before_Bake: bpy.props.BoolProperty(default=False)

    use_post_generation_script: bpy.props.BoolProperty(default=False)
    post_generation_script: bpy.props.PointerProperty(type=bpy.types.Text)



def Change_to_Baked_Name(context, item):
    scn = context.scene
    Action_Bakery = scn.GRT_Action_Bakery
    Settings = scn.GRT_Action_Bakery_Global_Settings

    name = None

    if item.Action:
        name = item.Action.name

        if item.use_Local_Name:
            name = item.LOCAL_Baked_Name
        else:
            if Settings.GLOBAL_Baked_Name_Mode == "SUFFIX":
                name = item.Action.name + Settings.GLOBAL_Baked_Name_01

            if Settings.GLOBAL_Baked_Name_Mode == "PREFIX":
                name = Settings.GLOBAL_Baked_Name_01 + item.Action.name

            if Settings.GLOBAL_Baked_Name_Mode == "REPLACE":
                name = item.Action.name.replace(
                    Settings.GLOBAL_Baked_Name_01, Settings.GLOBAL_Baked_Name_02
                )

    return name


def check_invalid_name(context):
    scn = context.scene
    Action_Bakery = scn.GRT_Action_Bakery

    Settings = scn.GRT_Action_Bakery_Global_Settings

    check = []

    if Settings.Overwrite:
        for item in Action_Bakery:
            if item.Action:
                if item.Action.name == Change_to_Baked_Name(context, item):
                    check.append(item)

    return check


def clear_pose(obj):
    for n in obj.pose.bones:
        n.location = (0, 0, 0)
        n.rotation_quaternion = (1, 0, 0, 0)
        n.rotation_axis_angle = (0, 0, 1, 0)
        n.rotation_euler = (0, 0, 0)
        n.scale = (1, 1, 1)


def get_selected_rig_pair(context):
    scn = context.scene

    if hasattr(scn, "GRT_Action_Bakery_Rig_Pairs"):
        index = scn.GRT_Action_Bakery_Rig_Pair_Index
        if 0 <= index < len(scn.GRT_Action_Bakery_Rig_Pairs):
            return scn.GRT_Action_Bakery_Rig_Pairs[index]

    return None


def get_selected_rig_pair_objects(context):
    settings = context.scene.GRT_Action_Bakery_Global_Settings
    pair = get_selected_rig_pair(context)

    if pair:
        if pair.Source_Armature != pair.Target_Armature:
            return pair.Source_Armature, pair.Target_Armature

    if settings.Source_Armature and settings.Target_Armature:
        if settings.Source_Armature != settings.Target_Armature:
            return settings.Source_Armature, settings.Target_Armature

    return None, None


def sync_selected_rig_pair_to_global_settings(context):
    settings = context.scene.GRT_Action_Bakery_Global_Settings
    control_rig, deform_rig = get_selected_rig_pair_objects(context)

    if control_rig:
        settings.Source_Armature = control_rig
    if deform_rig:
        settings.Target_Armature = deform_rig


def get_all_rig_pairs(context):
    scn = context.scene
    settings = scn.GRT_Action_Bakery_Global_Settings
    pairs = []

    for item in scn.GRT_Action_Bakery_Rig_Pairs:
        if item.Source_Armature and item.Target_Armature:
            if item.Source_Armature != item.Target_Armature:
                pairs.append((item.Source_Armature, item.Target_Armature))

    if len(pairs) == 0 and settings.Source_Armature and settings.Target_Armature:
        if settings.Source_Armature != settings.Target_Armature:
            pairs.append((settings.Source_Armature, settings.Target_Armature))

    return pairs


def get_rig_pairs(context):
    scn = context.scene
    settings = scn.GRT_Action_Bakery_Global_Settings
    pairs = []

    for item in scn.GRT_Action_Bakery_Rig_Pairs:
        if item.enabled and item.Source_Armature and item.Target_Armature:
            if item.Source_Armature != item.Target_Armature:
                pairs.append((item.Source_Armature, item.Target_Armature))

    if len(pairs) == 0 and settings.Source_Armature and settings.Target_Armature:
        if settings.Source_Armature != settings.Target_Armature:
            pairs.append((settings.Source_Armature, settings.Target_Armature))

    return pairs


def unique_objects(objects):
    unique = []
    for obj in objects:
        if obj and obj not in unique:
            unique.append(obj)
    return unique


def set_constraints_mute(obj, mute):
    if obj and obj.pose:
        for bone in obj.pose.bones:
            for constraint in bone.constraints:
                constraint.mute = mute


def action_slot_matches_object(slot, obj):
    slot_names = [
        getattr(slot, "name_display", ""),
        getattr(slot, "identifier", ""),
    ]
    expected_identifier = obj.id_type[:2] + obj.name

    for slot_name in slot_names:
        if slot_name in {obj.name, expected_identifier}:
            return True

    return False


def assign_action_to_object(obj, action):
    animation_data = obj.animation_data_create()

    if animation_data.use_tweak_mode:
        animation_data.use_tweak_mode = False

    animation_data.action = action

    action_slot = None
    for slot in animation_data.action_suitable_slots:
        if action_slot_matches_object(slot, obj):
            action_slot = slot
            break

    if action_slot is None:
        for slot in animation_data.action_suitable_slots:
            action_slot = slot
            break

    if action_slot is not None:
        animation_data.action_slot = action_slot


def find_action_slot_by_identifier(action, slot_identifier):
    if not action or not slot_identifier:
        return None

    for slot in getattr(action, "slots", []):
        if getattr(slot, "identifier", "") == slot_identifier:
            return slot

    return None


def ensure_action_slot_for_object(action, obj):
    for slot in getattr(action, "slots", []):
        if action_slot_matches_object(slot, obj):
            return slot

    return action.slots.new(obj.id_type, obj.name)


def assign_destination_action_to_object(obj, action):
    animation_data = obj.animation_data_create()

    if animation_data.use_tweak_mode:
        animation_data.use_tweak_mode = False

    animation_data.action = action
    animation_data.action_slot = ensure_action_slot_for_object(action, obj)


def make_destination_action(action_name, overwrite):
    if overwrite:
        existing_action = bpy.data.actions.get(action_name)
        if existing_action:
            bpy.data.actions.remove(existing_action, do_unlink=True)

    return bpy.data.actions.new(action_name)


def action_fcurves(action):
    if not action:
        return

    if hasattr(action, "layers") and len(action.layers) > 0:
        for layer in action.layers:
            for strip in layer.strips:
                for channelbag in strip.channelbags:
                    for fcurve in channelbag.fcurves:
                        yield fcurve
    else:
        for fcurve in action.fcurves:
            yield fcurve


def offset_action_to_frame_one(action):
    if not action:
        return

    start_frame = int(action.frame_range[0])
    for fcurve in action_fcurves(action):
        for kp in fcurve.keyframe_points:
            kp.co.x = kp.co.x - start_frame + 1


def push_action_to_nla(obj, action, overwrite):
    if not obj or not action:
        return

    animation_data = obj.animation_data_create()

    if overwrite:
        for track in animation_data.nla_tracks:
            if track.name == action.name:
                for _ in track.strips:
                    for strip in track.strips:
                        track.strips.remove(strip)
                        break

        for _ in animation_data.nla_tracks:
            for track in animation_data.nla_tracks:
                if len(track.strips) == 0 and track.name == action.name:
                    animation_data.nla_tracks.remove(track)
                    break

    track = animation_data.nla_tracks.new()
    track.name = action.name
    track.strips.new(action.name, int(action.frame_range[0]), action)


class GRT_Bake_Action_Bakery(bpy.types.Operator):
    bl_idname = "gamerigtool.bake_action_bakery"
    bl_label = "Bake Action Bakery"
    bl_info = {"UNDO", "REGISTER"}

    @classmethod
    def poll(cls, context):
        scn = context.scene

        if len(get_rig_pairs(context)) > 0:
            # return True

            if len(check_invalid_name(context)) == 0:
                return True

        return False

    def draw(self, context):
        layout = self.layout
        draw_global_bake_settings(layout, context)

    def invoke(self, context, event):
        scn = context.scene
        Global_Settings = scn.GRT_Action_Bakery_Global_Settings

        if Global_Settings.Bake_Popup:
            return context.window_manager.invoke_props_dialog(self)
        else:
            return self.execute(context)

    def execute(self, context):
        scn = context.scene

        Global_Settings = scn.GRT_Action_Bakery_Global_Settings
        Action_Bakery = scn.GRT_Action_Bakery

        rig_pairs = get_rig_pairs(context)
        control_rigs = unique_objects([pair[0] for pair in rig_pairs])
        deform_rigs = unique_objects([pair[1] for pair in rig_pairs])
        all_rigs = unique_objects(control_rigs + deform_rigs)
        animation_state = {}

        for obj in all_rigs:
            obj.hide_set(False)
            obj.hide_viewport = False

            if obj.animation_data:
                action = obj.animation_data.action
                action_slot = obj.animation_data.action_slot
                animation_state[obj] = {
                    "use_nla": obj.animation_data.use_nla,
                    "action_name": action.name if action else None,
                    "action_slot_identifier": (
                        action_slot.identifier if action_slot else None
                    ),
                }
                obj.animation_data.use_nla = False
            else:
                animation_state[obj] = {
                    "use_nla": None,
                    "action_name": None,
                    "action_slot_identifier": None,
                }

        try:
            if Global_Settings.GLOBAL_Clear_Transform_Before_Bake:
                for obj in all_rigs:
                    clear_pose(obj)

            for Baker in Action_Bakery:
                if not Baker.Action or not Baker.Bake_Select:
                    continue

                action = Baker.Action

                if Global_Settings.Pre_Unmute_Constraint:
                    for deform_rig in deform_rigs:
                        set_constraints_mute(deform_rig, False)

                for control_rig in control_rigs:
                    assign_action_to_object(control_rig, action)

                if Global_Settings.GLOBAL_Clear_Transform_Before_Bake:
                    for obj in all_rigs:
                        clear_pose(obj)

                action_name = Change_to_Baked_Name(context, Baker)
                if Baker.use_Local_Name and not Baker.LOCAL_Baked_Name:
                    action_name = "Baked_" + action.name

                if Baker.Frame_Range_Mode == "SET":
                    start_frame = Baker.Set_FR_Start
                    end_frame = Baker.Set_FR_End + 1
                if Baker.Frame_Range_Mode == "ACTION":
                    start_frame = int(action.frame_range[0])
                    end_frame = int(action.frame_range[1]) + 1
                if Baker.Frame_Range_Mode == "TRIM":
                    start_frame = int(action.frame_range[0]) + Baker.Trim_FR_Start
                    end_frame = int(action.frame_range[1]) + 1 - Baker.Trim_FR_End

                frame = [i for i in range(start_frame, end_frame)]
                context.scene.frame_current = start_frame

                destination_action = make_destination_action(
                    action_name, Global_Settings.Overwrite
                )
                for deform_rig in deform_rigs:
                    assign_destination_action_to_object(deform_rig, destination_action)

                obj_act = [
                    [deform_rig, destination_action] for deform_rig in deform_rigs
                ]

                Baked_Action = anim_utils.bake_action_objects(
                    obj_act,
                    frames=frame,
                    bake_options=anim_utils.BakeOptions(
                        only_selected=Global_Settings.BAKE_SETTINGS_Only_Selected,
                        do_pose=Global_Settings.BAKE_SETTINGS_Do_Pose,
                        do_object=Global_Settings.BAKE_SETTINGS_Do_Object,
                        do_visual_keying=Global_Settings.BAKE_SETTINGS_Do_Visual_Keying,
                        do_constraint_clear=Global_Settings.BAKE_SETTINGS_Do_Constraint_Clear,
                        do_parents_clear=Global_Settings.BAKE_SETTINGS_Do_Parent_Clear,
                        do_clean=Global_Settings.BAKE_SETTINGS_Do_Clean,
                        do_location=Global_Settings.BAKE_SETTINGS_Location,
                        do_rotation=Global_Settings.BAKE_SETTINGS_Rotation,
                        do_scale=Global_Settings.BAKE_SETTINGS_Scale,
                        do_bbone=Global_Settings.BAKE_SETTINGS_BBone,
                        do_custom_props=Global_Settings.BAKE_SETTINGS_Custom_Properties,
                    ),
                )

                baked_action = next(
                    (baked_action for baked_action in Baked_Action if baked_action),
                    destination_action,
                )
                baked_action.name = action_name

                if Baker.offset_keyframe_to_frame_one:
                    offset_action_to_frame_one(baked_action)

                context.view_layer.update()

                if Global_Settings.Push_to_NLA:
                    for deform_rig in deform_rigs:
                        push_action_to_nla(
                            deform_rig, baked_action, Global_Settings.Overwrite
                        )

                if Global_Settings.Post_Mute_Constraint:
                    for deform_rig in deform_rigs:
                        set_constraints_mute(deform_rig, True)
        finally:
            for control_rig in control_rigs:
                if control_rig.animation_data:
                    saved_action_name = animation_state[control_rig]["action_name"]
                    saved_action = (
                        bpy.data.actions.get(saved_action_name)
                        if saved_action_name
                        else None
                    )
                    control_rig.animation_data.action = saved_action
                    if saved_action:
                        saved_slot = find_action_slot_by_identifier(
                            saved_action,
                            animation_state[control_rig]["action_slot_identifier"],
                        )
                        if saved_slot:
                            control_rig.animation_data.action_slot = saved_slot

            for deform_rig in deform_rigs:
                if deform_rig.animation_data:
                    deform_rig.animation_data.action = None

            for obj in all_rigs:
                if obj.animation_data:
                    saved_use_nla = animation_state[obj]["use_nla"]
                    if saved_use_nla is not None:
                        obj.animation_data.use_nla = saved_use_nla

            if context.mode != "OBJECT":
                bpy.ops.object.mode_set(mode="OBJECT")

            bpy.ops.object.select_all(action="DESELECT")
            for deform_rig in deform_rigs:
                deform_rig.hide_set(False)
                deform_rig.hide_viewport = False
                deform_rig.select_set(True)
            for control_rig in control_rigs:
                control_rig.hide_set(True)
                control_rig.hide_viewport = True
            if deform_rigs:
                context.view_layer.objects.active = deform_rigs[0]

        return {"FINISHED"}


classes = [
    GRT_Action_Bakery_Set_Frame_Range_To_Action,
    GRT_Load_Action_Menu,
    GRT_Bake_Action_Bakery,
    GRT_Action_Bakery_Rig_Pair_List_Operator,
    GRT_Action_Bakery_List_Operator,
    GRT_UL_Action_Bakery_List,
    GRT_UL_Action_Bakery_Rig_Pair_List,
    GRT_Action_Bakery_Property_Group,
    GRT_Action_Bakery_Rig_Pair_Property_Group,
    GRT_Action_Bakery_Global_Settings_Property_Group,
    GRT_PT_Action_Bakery,
    GRT_OT_Toggle_Rig,
]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.Scene.GRT_Action_Bakery = bpy.props.CollectionProperty(
        type=GRT_Action_Bakery_Property_Group
    )
    bpy.types.Scene.GRT_Action_Bakery_Index = bpy.props.IntProperty()
    bpy.types.Scene.GRT_Action_Bakery_Rig_Pairs = bpy.props.CollectionProperty(
        type=GRT_Action_Bakery_Rig_Pair_Property_Group
    )
    bpy.types.Scene.GRT_Action_Bakery_Rig_Pair_Index = bpy.props.IntProperty()

    bpy.types.Scene.GRT_Action_Bakery_Global_Settings = bpy.props.PointerProperty(
        type=GRT_Action_Bakery_Global_Settings_Property_Group
    )


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    del bpy.types.Scene.GRT_Action_Bakery
    del bpy.types.Scene.GRT_Action_Bakery_Index
    del bpy.types.Scene.GRT_Action_Bakery_Rig_Pairs
    del bpy.types.Scene.GRT_Action_Bakery_Rig_Pair_Index
    del bpy.types.Scene.GRT_Action_Bakery_Global_Settings


if __name__ == "__main__":
    register()
