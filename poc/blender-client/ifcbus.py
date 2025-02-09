import bpy

import bmesh
from bpy_extras.object_utils import AddObjectHelper
from bpy_extras import object_utils

from time import sleep
from uuid import uuid4
from ifc_databus.core.bus import IfcBus

from compas_eve import set_default_transport
from compas_eve.mqtt import MqttTransport

import json 
import copy

Bus = None
timer_freq = 1

p = "../message/example_message_wall_mesh.json"
f = open(p)
d = json.load(f)

def scaledown(verts):
    for v in verts:
        v[0] = v[0] * .001
        v[1] = v[1] * .001
        v[2] = v[2] * .001

def read_json_stream(jsondata):
    import ast
    item = jsondata.data
    print(item)
    print(item)
    print(item['type'])
    if item['type'] == "IfcWall":
        reps = item["representation"]
        reps = ast.literal_eval(reps)
        for r in reps["representations"]:
            for i in r["items"]:
                if i["type"] == "IfcTriangulatedFaceSet":
                    vdata = i["coordinates"]
                    v = copy.copy(vdata["coordList"])
                    print("vertices",v)
                    f = copy.copy(i["coordIndex"])
                    print("faces",f)
                    return v,f
        return None

def read_json_data(jsondata):
    for item in jsondata['data']:
        if item['type'] == "IfcWall":
            for data in item:
                print("DATA:")
                print(data)
                if data == "representation":
                    rep = item[data]
                    #print(rep)
                    for d in rep:
                        #print(d)
                        if d == "representations":
                            obj = rep[d]
                            #print(obj)
                            for p in obj:
                                for i in p:
                                    if i == "items":
                                        for j in p[i]:
                                            for k in j:
                                                if k == "type":
                                                    if j[k] == "IfcTriangulatedFaceSet":
                                                        vdata = j["coordinates"]
                                                        v = copy.copy(vdata["coordList"])
                                                        print("vertices",v)
                                                        f = copy.copy(j["coordIndex"])
                                                        print("faces",f)
                                                        return v,f
        return None


class IfcBusConnect(bpy.types.Operator,AddObjectHelper):
    """IfcBusConnect"""
    bl_idname = "scene.ifcbus_connect"
    bl_label = "Connect"

    def get_object(self,_id):
        for obj in bpy.data.objects:
            if obj.name == _id:
                return obj

    def add_object(self,context,_id,mesh):
        print(bpy.context.object)
        object_utils.object_data_add(context, mesh, operator=self, name=_id)
        print("added:",_id)

    def update_wall(self,reg):
        print()

    def update_object(self,context,reg):

        _id = reg.replica_id
        obj = self.get_object(_id)

        if obj != None:
            print(obj.name)
            sc = bpy.data.scenes["Scene"]
            objs = bpy.data.objects
            objs.remove(objs[_id], do_unlink=True)
            meshes = bpy.data.meshes
            meshes.remove(meshes[_id], do_unlink=True)
            print("removed:",_id)
            bpy.ops.object.select_all(action='DESELECT')


        data = read_json_stream(reg)
        if data is None:
            return

        verts_loc,faces = data
        scaledown(verts_loc)

        mesh = bpy.data.meshes.new(_id)
        bm = bmesh.new()

        for v_co in verts_loc:
            bm.verts.new(v_co)

        bm.verts.ensure_lookup_table()
        for f_idx in faces:
            bm.faces.new([bm.verts[i] for i in f_idx])

        bm.to_mesh(mesh)
        mesh.update()

        self.add_object(context,_id,mesh)


    def modal(self,context,event):
        print(event.type)
        if event.type == 'TIMER':
            if Bus != None:
                cp = copy.copy(Bus._registers) 
                for i in cp:
                    reg = Bus._registers[i]
                    t = reg.entity_type
                    self.update_object(context,reg)

        return {'PASS_THROUGH'}

    def execute(self, context):
        #set_default_transport(MqttTransport("localhost", 1883))
        set_default_transport(MqttTransport("85.215.121.128", 1883))
        global Bus

        if Bus == None:
            wm = context.window_manager
            self._timer = wm.event_timer_add(1, window=context.window)
            wm.modal_handler_add(self)

        Bus = IfcBus("mainbus")
        Bus.connect()

        return {'RUNNING_MODAL'}

def menu_func(self, context):
    self.layout.operator(IfcBusTest.bl_idname, text=IfcBusTest.bl_label)

def register_operator():
    bpy.utils.register_class(IfcBusConnect)
    bpy.types.VIEW3D_MT_object.append(menu_func)


def unregister_operator():
    bpy.utils.unregister_class(IfcBusConnect)
    bpy.types.VIEW3D_MT_object.remove(menu_func)

##########################################################
# UI
##########################################################

class IfcBusUI(bpy.types.Panel):
    """IfcBus"""
    bl_label = "IfcBus"
    bl_idname = "OBJECT_PT_IFCBUS"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.operator("scene.ifcbus_connect")


def register_ui():
    bpy.utils.register_class(IfcBusUI)


def unregister_ui():
    bpy.utils.unregister_class(IfcBusUI)


if __name__ == "__main__":
    register_ui()
    register_operator()
