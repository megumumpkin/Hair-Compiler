import bpy
from bpy.app.handlers import persistent

class HairCompilerData(bpy.types.PropertyGroup):
    curve_steps : bpy.props.IntProperty(name="Curve Steps", default=0, min=0)
    start_offset : bpy.props.IntProperty(name="Rig start offset", default=0, min=0)

classes = [
    HairCompilerData
]

def register():
    for c in classes:
        bpy.utils.register_class(c)

    bpy.types.Curve.haircompiler_data = bpy.props.PointerProperty(type=HairCompilerData, options={'HIDDEN'})

def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)

    del bpy.types.Curve.haircompiler_data