# Hair compiler, create mesh hair rigs for in-engine simulation, uses VRM-like solution for hair joint simulation

import bpy
from . import scenedata
from . import operator
from . import ui

bl_info = {
    "name" : "Hair Compiler",
    "author" : "megumumpkin",
    "blender" : (3,6,0),
    "version" : (2023,1),
    "location" : "View3D",
    "category" : "Rigging"
}

register, unregister = bpy.utils.register_submodule_factory(__package__, [
    'scenedata',
    'operator',
    'ui'
])

# def register():
#     scenedata.register()
#     operator.register()
#     ui.register()
# def unregister():
#     ui.unregister()
#     operator.unregister()
#     scenedata.unregister()

# if __name__ == '__main__':
#     register()