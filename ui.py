import bpy
from bpy.types import Panel

class HAIRCOMPILER_PT_panel(Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_label = "Hair Compiler"
    bl_category = "Hair Compiler"

    def draw(self, context):
        layout = self.layout
        # layout.prop(bpy.context.scene, "muramasa_project_root")
        # layout.operator("muramasa.interlink_op_updateasset")
        if(type(bpy.context.object.data) == bpy.types.Curve):
            layout.operator("haircompiler.op_generate_rig")
            layout.label(text="Curve's Resolution U:  "+str(bpy.context.object.data.resolution_u))
            layout.prop(bpy.context.object.data.haircompiler_data, "curve_steps")
            layout.prop(bpy.context.object.data.haircompiler_data, "start_offset")

classes = [
    HAIRCOMPILER_PT_panel
]

def register():
    for c in classes:
        bpy.utils.register_class(c)

def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)