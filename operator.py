import bpy
import bmesh
import mathutils
from bpy.types import Operator

# Hair Generator helper functions

def _internal_SplitCurves(context):
    obj = context.object
    for i in range (len(obj.data.splines)):
        spline = obj.data.splines[i]
        for j in range(len(spline.bezier_points)):
            bezier_point = spline.bezier_points[j]
            bezier_point.select_left_handle = False
            bezier_point.select_right_handle = False
            bezier_point.select_control_point = False
        
    bpy.ops.object.editmode_toggle()
    while (len(obj.data.splines)) > 0:
        spline = obj.data.splines[0]
        for j in range(len(spline.bezier_points)):
            bezier_point = spline.bezier_points[j]
            bezier_point.select_control_point = True

        bpy.ops.curve.select_linked()
        bpy.ops.curve.separate(confirm=False)

    bpy.ops.object.editmode_toggle()

    obj.select_set(False)

    return context.view_layer.objects.selected.values()

# Original source code by Leander: https://blender.stackexchange.com/questions/69011/how-to-convert-curve-to-armature
def _internal_CreateChainFromVertices(context, start_offset, switch_direction = False):
    # scene = context.scene
    obj = context.object

    if(start_offset > 1):
        switch_direction = not switch_direction
        bpy.ops.object.mode_set(mode='EDIT')
        edit_mesh = bmesh.from_edit_mesh(obj.data)
        if(start_offset < len(edit_mesh.verts)):
            vert_selection = []
            for i in range(start_offset):
                if hasattr(edit_mesh.verts, "ensure_lookup_table"):
                    edit_mesh.verts.ensure_lookup_table()
                vert_selection.append(edit_mesh.verts[i])
                # edit_mesh.verts[i].select_set(True)
                # edit_mesh.select_history.add(edit_mesh.verts[i])            
            bmesh.ops.pointmerge(edit_mesh, verts=vert_selection, merge_co=vert_selection[0].co)
            bmesh.update_edit_mesh(obj.data)
            # bpy.ops.mesh.merge(type='FIRST', uvs=False)

    bpy.ops.object.mode_set(mode='OBJECT')
    edgesA = []
    edgesB = []
    for i in range(len(obj.data.edges)):
        vtx = obj.data.edges[i].vertices
        edgesA.append(vtx[0])
        edgesB.append(vtx[1])

    chain = []
    chain.append(edgesA[0])
    while(True):
        current = chain[len(chain)-1]
        if current in edgesA:
            idx = edgesA.index(current)
            next = edgesB[idx]
            del edgesA[idx]
            del edgesB[idx]
            chain.append(next)
        elif current in edgesB:
            idx = edgesB.index(current)
            next = edgesA[idx]
            del edgesA[idx]
            del edgesB[idx] 
            chain.append(next)
        else:
            if (chain[0] in edgesA) or (chain[0] in edgesB):
                chain = list(reversed(chain))
            else:
                break
    if switch_direction:
        chain = list(reversed(chain))
    
    armature = bpy.data.armatures.new(obj.name + "_bones")
    rig = bpy.data.objects.new(obj.name + "_rig", armature)
    context.collection.objects.link(rig)
    context.view_layer.objects.active = rig
    rig.select_set(True)

    bpy.ops.object.editmode_toggle()
    for i in range(0, len(chain) - 1):
        bone = armature.edit_bones.new(obj.name+"_bone_"+str(i+1))
        bone.head = obj.data.vertices[chain[i]].co
        bone.tail = obj.data.vertices[chain[i + 1]].co
    for i in range(0, len(armature.edit_bones) - 1):
        armature.edit_bones[i + 1].parent = armature.edit_bones[i]
        armature.edit_bones[i + 1].use_connect = True
    bpy.ops.object.editmode_toggle()

    rig.select_set(False)

    return rig

def _internal_GenerateOneRig(context):
    name = context.object.name
    original = context.object

    bpy.ops.object.duplicate(linked=False, mode='TRANSLATION')
    cloned_curve = context.view_layer.objects.active

    # Get all curves
    curvelist = _internal_SplitCurves(context)
    bpy.ops.object.select_all(action='DESELECT')
    
    cloned_curve.select_set(True)
    context.view_layer.objects.active = cloned_curve
    bpy.ops.object.delete(use_global=True, confirm=False)

    # Clone to be converted to bones
    for i in range(len(curvelist)):
        curve = curvelist[i]
        curve.name = name+"_mesh_"+str(i+1)
        curve.select_set(True)
    bpy.ops.object.duplicate(linked=False, mode='TRANSLATION')
    for curve in curvelist:
        curve.select_set(False)

    curvesimplelist = context.view_layer.objects.selected.values()

    bpy.ops.object.select_all(action='DESELECT')

    # Clone to be converted to bones
    for curve in curvelist:
        curve.select_set(True)
    bpy.ops.object.duplicate(linked=False, mode='TRANSLATION')
    for curve in curvelist:
        curve.select_set(False)

    genriglist = context.view_layer.objects.selected.values()

    # Get all bones
    riglist = []
    for i in range(len(genriglist)):
        genrig = genriglist[i]
        genrig.name = name+"_rig_"+str(i+1)
        genrig.data.resolution_u = original.data.haircompiler_data.curve_steps
        genrig.data.bevel_mode = 'ROUND'
        genrig.data.bevel_depth = 0.0
    context.view_layer.objects.active = genriglist[0]
    bpy.ops.object.convert(target='MESH')
    for genrig in genriglist:
        context.view_layer.objects.active = genrig
        riglist.append(_internal_CreateChainFromVertices(context, start_offset=original.data.haircompiler_data.start_offset))

    # Delete all converted meshes
    bpy.ops.object.select_all(action='DESELECT')
    for genrig in genriglist:
        genrig.select_set(True)
    bpy.ops.object.delete(use_global=True, confirm=False)
    bpy.ops.object.select_all(action='DESELECT')

    # Selectively auto rig all pairs
    for i in range(len(curvelist)):
        curve = curvelist[i]
        curve_simple = curvesimplelist[i]
        rig = riglist[i]

        # Simplified curves rig
        curve_simple.select_set(True)
        curve_simple.data.resolution_u = original.data.haircompiler_data.curve_steps
        context.view_layer.objects.active = curve_simple
        bpy.ops.object.convert(target='MESH')

        rig.select_set(True)
        context.view_layer.objects.active = rig
        bpy.ops.object.parent_set(type='ARMATURE_AUTO', xmirror=False, keep_transform=False)
        bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')

        curve_simple.select_set(False)
        rig.select_set(False)

        # Final curve rig, name only
        curve.select_set(True)
        context.view_layer.objects.active = curve
        bpy.ops.object.convert(target='MESH')
        
        rig.select_set(True)
        context.view_layer.objects.active = rig
        bpy.ops.object.parent_set(type='ARMATURE_NAME', xmirror=False, keep_transform=False)
        bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')

        curve.select_set(False)
        rig.select_set(False)

        # Transfer simplified curves vertex weights data to the final one
        curve.select_set(True)
        context.view_layer.objects.active = curve
        data_transfer = curve.modifiers.new(name="DTRA", type='DATA_TRANSFER')
        data_transfer.object = curve_simple
        data_transfer.use_vert_data = True
        data_transfer.data_types_verts = {'VGROUP_WEIGHTS'}
        data_transfer.vert_mapping = 'POLYINTERP_NEAREST'
        bpy.ops.object.convert(target='MESH')

        curve.select_set(False)

        curve_simple.select_set(True)
        context.view_layer.objects.active = curve_simple
        bpy.ops.object.delete(use_global=True, confirm=False)

    # Join all bones into one
    for rig in riglist:
        rig.select_set(True)
    final_armature = riglist[0]
    final_armature.name = name+"_rig"
    context.view_layer.objects.active = final_armature
    bpy.ops.object.join()
    riglist = []

    bpy.ops.object.select_all(action='DESELECT')

    # Join all curves into one again
    for curve in curvelist:
        curve.select_set(True)
    final_curve = curvelist[0]
    final_curve.name = name+"_hair"
    context.view_layer.objects.active = final_curve
    bpy.ops.object.join()

    bpy.ops.object.select_all(action='DESELECT')

    final_curve.select_set(True)
    final_armature.select_set(True)
    context.view_layer.objects.active = final_armature

    bpy.ops.object.parent_set(type='ARMATURE_NAME', xmirror=False, keep_transform=False)

    bpy.ops.object.select_all(action='DESELECT')

    return { "armature" : final_armature, "curve" : final_curve }


class HAIRCOMPILER_OT_genrig(Operator):
    bl_idname = "haircompiler.op_generate_rig"
    bl_label = "Generate Hair Mesh Rig"
    bl_description = "Generate Hair Mesh Rig Usable for Realtime Engines"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        for object in context.view_layer.objects.selected.values():
            if type(context.object.data) is not bpy.types.Curve:
                return False

        return True
    
    def execute(self, context):
        part_list = context.view_layer.objects.selected.values()
        bpy.ops.object.select_all(action='DESELECT')
        
        armatures = []
        curves = []
        for part in part_list:
            part.select_set(True)
            context.view_layer.objects.active = part
            result = _internal_GenerateOneRig(context)
            armatures.append(result["armature"])
            curves.append(result["curve"])
        
        for armature in armatures:
            armature.select_set(True)
        final_armature = armatures[0]
        context.view_layer.objects.active = final_armature
        bpy.ops.object.join()
        armatures = []

        bpy.ops.object.select_all(action='DESELECT')

        for curve in curves:
            curve.select_set(True)
        final_curve = curves[0]
        context.view_layer.objects.active = final_curve
        bpy.ops.object.join()
        curves = []

        final_armature.select_set(True)
        context.view_layer.objects.active = final_armature

        bpy.ops.object.parent_set(type='ARMATURE_NAME', xmirror=False, keep_transform=False)
    
        return {'FINISHED'}
        ''

class HAIRCOMPILER_OT_stub(Operator):
    bl_idname = "haircompiler.op_stub"
    bl_label = "Generate Hair Mesh Rig"
    bl_description = "Generate Hair Mesh Rig Usable for Realtime Engines"

    @classmethod
    def poll(cls, context):
        return True
    
    def execute(self, context):
        return {'FINISHED'}

classes = [
    HAIRCOMPILER_OT_genrig,
    HAIRCOMPILER_OT_stub
]

def register():
    for c in classes:
        bpy.utils.register_class(c)

def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)