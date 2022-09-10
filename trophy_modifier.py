
bl_info = {
    "name": "PES/WE/JL PS2 Trophy Modifier Tool",
    "author": "PES Indie Team",
    "version": (1,0),
    "blender": (2, 6, 7),
    "api": 35853,
    "location": "Under Scene Tab",
    "description": "Import/Export PES/WE/JL PS2 Trophy Model",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "System"}

import bpy,bmesh,zlib,os,struct,io
from bpy.props import *

bpy.types.Scene.face_path = StringProperty(name="Trophy File",subtype='FILE_PATH',default="Select the Trophy BIN File from here   --->")
bpy.types.Scene.pes_ver = EnumProperty(name="Select PES Version",items=[("pes_ps2","PES/WE PS2"," ")], default="pes_ps2")
bpy.types.Scene.uv_sw = BoolProperty(name="", default=False)
bpy.types.Scene.face_vc = IntProperty(name="", default=0)
tool_id="PES/WE/JL PS2 Trophy Modifier Tool v1.0 - Blender v2.67"
facepath,face_id, = "","",
temp_folder = bpy.app[4].split('blender.exe')[0]+'pes_temp\\'
face_temp = temp_folder+"trophy_unzlib_temp"
pes_ps2_vc = 0

def unzlib(model):
    
    if model == 'face':
        filepath_imp=facepath
        temp=face_temp
        
    data1 = open(filepath_imp, 'rb')
    data1.seek(32,0)
    data2=data1.read()
    data3=zlib.decompress(data2,32)
    out=open(temp,"wb")
    out.write(data3)
    out.flush()
    out.close()
    
    return open(temp,"rb")

def zlib_comp(model):
    
    if model == 'face':
        filepath_exp=facepath
        temp=face_temp
    
    exp1=open(temp, 'rb').read()
    exp2=zlib.compress(exp1,9)
    s1,s2=len(exp1),len(exp2)
    exp=open(filepath_exp,"wb")
    exp.write(struct.pack("I",0x00010600))
    exp.write(struct.pack("I",s2))
    exp.write(struct.pack("I",s1))
    exp.write(struct.pack("20s","".encode()))
    exp.write(exp2)
    exp.write(struct.pack("16s","".encode()))
    copyright = "Made by PES Indie Team"
    exp.write(struct.pack("I50sI28s",0,
                              tool_id.encode(),
                              0,copyright.encode()))
    exp.flush()
    exp.close()


def pes_ps2_exp(self,model):

    global pes_ps2_vc

    if model == 'face':
        temp=face_temp
        obname='PES_PS2_Trophy'
        pes_ps2_vc=bpy.context.scene.face_vc
    ### Export Model ###

    ex6_file=open(temp,"r+b")
    for ob in bpy.data.objects:
        if ob.name[:14] == obname:
            if ob.hide == 0:
                bpy.context.scene.objects.active=ob
    ac_ob=bpy.context.active_object
    data=ac_ob.data

    if len(data.vertices) != pes_ps2_vc:
        print("")
        self.report( {"ERROR"}, "Vertex Count is Not Equal with Base Model !!\nDont delete or add any vertices !!\nTry Import again Base Model !!\nInfo: Base Model is always last imported model...  " )
        return 0

    uvlayer=data.uv_layers.active.data 
    vidx_list,exp_uvlist=[],[]

    for poly in data.polygons:
        for idx in range(poly.loop_start, poly.loop_start + poly.loop_total):
            if data.loops[idx].vertex_index not in vidx_list:
                vidx_list.append(data.loops[idx].vertex_index)
                exp_uvlist.append((uvlayer[idx].uv[0],uvlayer[idx].uv[1]))


    ex6_file.seek(8,0)
    offset_file_1 = struct.unpack("<I", ex6_file.read(4))[0]
    ex6_file.seek(offset_file_1,0)
    if ex6_file.read(4) == bytearray([0x00, 0x06, 0x00, 0x00,]):
        offset_file_1 += 32
    ex6_file.seek(offset_file_1, 0)
    ex6_file.seek(8,1)
    offset_mdl_1 = struct.unpack("<I", ex6_file.read(4))[0] + offset_file_1
    #offset_mdl_1 = struct.unpack("<I", ex6_file.read(4))[0]




    parts_info_offset = 32
    vertex_in_part_offset = 88
    ex6_file.seek(offset_mdl_1 + parts_info_offset,0)
    total_parts, part_start_offset = struct.unpack("<II", ex6_file.read(8))
    part_start_offset += offset_mdl_1

    factor = 0.001553
    factor_uv = 0.000244 
    i = 0
    vertex_count = 0
    vertices_texture = []
    while i < total_parts:
        #print("part ",i, " offset: ", part_start_offset)
        ex6_file.seek(part_start_offset,0)
        part_size = struct.unpack("<I", ex6_file.read(4))[0]

        #print("part #", i)
        ex6_file.seek(4,1)
        part_info_start = struct.unpack("<I", ex6_file.read(4))[0]-12
        ex6_file.seek(part_info_start+vertex_in_part_offset,1)


        vertex_in_piece = struct.unpack("<H", ex6_file.read(2))[0]
        ex6_file.read(2)
        ex6_file.seek(8,1)
        for j in range(vertex_in_piece):
            x,y,z=data.vertices[vertex_count + j].co
            x,y,z = round(x/factor), round(y/factor), round((z)/factor)
            ex6_file.write(struct.pack("3h",x, z, y*-1))
            for t in vidx_list:
                if t == j + vertex_count:
                    u,v = exp_uvlist[vidx_list.index(t)][0],exp_uvlist[vidx_list.index(t)][1]
                    vertices_texture.append((u,v))

        #"""
        if vertex_in_piece%2!=0:
            # if the number of vertes is not pair then we need to incress the movement of bytes by two
            ex6_file.seek(2,1)
        # here we skip the normals
        ex6_file.seek(4,1)
        ex6_file.seek(vertex_in_piece*6,1)

        if vertex_in_piece%2!=0:
            # if the number of vertes is not pair then we need to incress the movement of bytes by two
            ex6_file.seek(2,1)

        ex6_file.seek(4,1)
        for j in range(vertex_in_piece):
            u, v = round((vertices_texture[vertex_count + j][0])/factor_uv), round((1 - vertices_texture[vertex_count + j][1]) / factor_uv)
            ex6_file.write(struct.pack("2h",u,v))

        part_start_offset += part_size
        i += 1
        vertex_count += vertex_in_piece

    ex6_file.flush()
    ex6_file.close()

    zlib_comp(model)

    return 1


def pes_ps2_imp(self,context,model):
    
    #if model == 'face':
    obname="PES_PS2_Trophy"
    imgfile=facepath        
        
    global pes_ps2_vc
    
    vlist,flist,edges,uvlist=[],[],[],[]
    
    file=unzlib(model) 
    
    file.seek(8,0)
    offset_file_1 = struct.unpack("<I", file.read(4))[0]
    file.seek(offset_file_1,0)
    if file.read(4) == bytearray([0x00, 0x06, 0x00, 0x00,]):
        offset_file_1 += 32
    file.seek(offset_file_1, 0)
    file.seek(8,1)
    offset_mdl_1 = struct.unpack("<I", file.read(4))[0] + offset_file_1
    
    #offset_mdl_1 = struct.unpack("<I", file.read(4))[0]
    
    parts_info_offset = 32
    vertex_in_part_offset = 88
    file.seek(offset_mdl_1 + parts_info_offset,0)
    total_parts, part_start_offset = struct.unpack("<II", file.read(8))
    part_start_offset += offset_mdl_1
    
    factor = 0.001553
    factor_uv = 0.000244
    i = 0
    vertex_count = 0

    while i < total_parts:
        #print("part ",i, " offset: ", part_start_offset)
        file.seek(part_start_offset,0)
        part_size = struct.unpack("<I", file.read(4))[0]

        file.seek(4,1)
        part_info_start = struct.unpack("<I", file.read(4))[0]-12
        file.seek(part_info_start + vertex_in_part_offset,1)
        

        vertex_in_piece = struct.unpack("<H", file.read(2))[0]
        file.read(2)
        file.seek(8,1)
        for j in range(vertex_in_piece):
            x, z, y = struct.unpack("<hhh", file.read(6))
            vlist.append(( ((x) * factor), ((y*-1) * factor), (z * factor) ))
        #"""
        if vertex_in_piece%2!=0:
            # if the number of vertes is not pair then we need to incress the movement of bytes by two
            file.seek(2,1)
        # Skip normals
        file.seek(4,1)
        file.seek(vertex_in_piece*6,1)
        
        if vertex_in_piece%2!=0:
            # if the number of vertes is not pair then we need to incress the movement of bytes by two
            file.seek(2,1)
            
        file.seek(4,1)
        for j in range(vertex_in_piece):
            u,v = struct.unpack("<hh", file.read(4))
            uvlist.append((u * factor_uv, 1 - v * factor_uv))
        end_of_part = part_start_offset + part_size
        end_data = file.read(end_of_part - file.tell())
        tri_start = end_data.find(bytes([0x01, 0x00, 0x00, 0x05, 0x01, 0x01, 0x00, 0x01]))
        tri_bytes = io.BytesIO(end_data[tri_start:])
        tri_strip_list_idx = tri_bytes.read(8)
        if tri_strip_list_idx != bytes([0x01, 0x00, 0x00, 0x05, 0x01, 0x01, 0x00, 0x01]):
            self.report( {"ERROR"}, "Triangles identifier doesn't match must be a wrong model or an error with this script, read was: " + str(tri_strip_list_idx) )
        tri_bytes.read(2)
        tri_list_size = (struct.unpack("<H", tri_bytes.read(2))[0] - 27904) * 8
        tri_data = tri_bytes.read(tri_list_size)
        tstrip_index_list = [int(idx/4) for idx in struct.unpack("<%dh" % int(len(tri_data)/2), tri_data)]

        for f in range(len(tstrip_index_list)-2):
            if(tstrip_index_list[f]<0 and tstrip_index_list[f+1]<0 and tstrip_index_list[f+2]>=0):
                if (tstrip_index_list[f] != tstrip_index_list[f+1]) and (tstrip_index_list[f+1] != tstrip_index_list[f+2]) and (tstrip_index_list[f+2] != tstrip_index_list[f]):
                    flist.append((8192 + tstrip_index_list[f] + vertex_count - 1, 8192 + tstrip_index_list[f+1] + vertex_count - 1, tstrip_index_list[f+2] + vertex_count - 1))
            elif(tstrip_index_list[f]<=0 and tstrip_index_list[f+1]>=0 and tstrip_index_list[f+2]>=0):
                if (tstrip_index_list[f] != tstrip_index_list[f+1]) and (tstrip_index_list[f+1] != tstrip_index_list[f+2]) and (tstrip_index_list[f+2] != tstrip_index_list[f]):
                    flist.append((8192 + tstrip_index_list[f] + vertex_count - 1, tstrip_index_list[f+1] + vertex_count - 1, tstrip_index_list[f+2] + vertex_count - 1))
            elif(tstrip_index_list[f+2]>=0 and tstrip_index_list[f+1]>=0 and tstrip_index_list[f]>0):
                if (tstrip_index_list[f+2] != tstrip_index_list[f+1]) and (tstrip_index_list[f+0] != tstrip_index_list[f+2]) and (tstrip_index_list[f+2] != tstrip_index_list[f]):    
                    flist.append((tstrip_index_list[f] + vertex_count - 1, tstrip_index_list[f+1] + vertex_count - 1, tstrip_index_list[f+2] + vertex_count - 1))
            else:
                continue

        part_start_offset += part_size
        i += 1
        vertex_count += vertex_in_piece

    pes_ps2_vc=vertex_count
    #if model == 'face':
    bpy.context.scene.face_vc=pes_ps2_vc
    
    file.flush()
    file.close()
    faces=flist
    mesh = bpy.data.meshes.new(obname)
    mesh.from_pydata(vlist, edges, faces)
    
    from bpy_extras import object_utils
    object_utils.object_data_add(context, mesh, operator=None)
    
    me=bpy.context.active_object.data
    bpy.ops.mesh.uv_texture_add('EXEC_SCREEN')
    bm = bmesh.new() 
    bm.from_mesh(me) 
    uv_layer = bm.loops.layers.uv.verify()
    
    for f in range(len(bm.faces)):
        for i in range(len(bm.faces[f].loops)):
            fuv=bm.faces[f].loops[i][uv_layer]
            fuv.uv = uvlist[faces[f][i]]
    bm.to_mesh(me)
    bm.free()
    
    bpy.ops.object.editmode_toggle()
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.editmode_toggle()
    
    ac_ob=bpy.context.active_object
    ac_ob.location=(0,0,0)
    
    imgid=bpy.path.display_name_from_filepath(imgfile)+'.bin_0.png'
    imgfile=imgfile[:-4]+'.bin_0.png'
    
    if os.access(imgfile,0) == 1:
    
        bpy.ops.image.open(filepath=imgfile,relative_path=False)
        img=bpy.data.images[imgid]
        uvdata=me.uv_textures[0].data
        for face in uvdata:
            face.image=img
    
    add_mat(ac_ob,model)

def add_mat(ac_ob,model):
    
    #if model == 'face':
        #obname="Face"
        #texname="face_tex"
    
    ### Add Material ###
    if len(bpy.data.materials) == 0:
        bpy.ops.material.new()
    matname='mat_trophy'
    bpy.data.materials[0].name=matname
    bpy.data.materials[matname].use_face_texture=1 
    bpy.data.materials[matname].game_settings.use_backface_culling = 0
    bpy.data.materials[matname].game_settings.alpha_blend='CLIP'
    bpy.data.materials[matname].use_face_texture_alpha=1
    
    bpy.context.active_object.data.materials.append(bpy.data.materials[matname])
    bpy.context.scene.game_settings.material_mode = 'MULTITEXTURE'
    #if bpy.context.scene.pes_ver != 'pes_pc' and bpy.context.scene.pes_ver != 'pes_ps2' and bpy.context.scene.pes_ver != 'pes_psp':
    #    bpy.data.images[texname].reload()
    bpy.context.scene.uv_sw = 0
    #if model == 'face':
    bpy.context.scene.face_vc = len(ac_ob.data.vertices)


class Face_Modifier_PA(bpy.types.Panel):
    bl_label = "PES/WE/JL PS2 Trophy Modifier"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"
    
    
    def draw(self, context):
        
        global facepath,face_id
        
        obj = bpy.context.active_object
        if obj:
            if obj.active_material:
                game = obj.active_material.game_settings
        scn = bpy.context.scene
        layout = self.layout
        
        for i in range(2):
            row=layout.row()
        row.label()
        row.prop(scn,"pes_ver",text="Game",icon='GAME')
        
        if scn.pes_ver == 'pes_ps2':
            for i in range(4):
                row=layout.row()
            box=layout.box()
            box.label(text="PES/WE PS2 Mode Supports Only 3D Model Import/Export",icon='INFO')
            box.label(text="Put Textures in Same Folder with the name assigned by WE Picture Decoder",icon='INFO')
            box.label(text="Ex: unnamed_95.bin = unnamed_95.bin_0.png (Auto-Import)",icon='INFO') 
        
        ## Trophy Panel
        for i in range(4):
            row=layout.row()
        box=layout.box()
        box.label(text="Trophy BIN File :")
        box.prop(scn,"face_path",text="")
        facepath=bpy.path.abspath(scn.face_path)
        face_id=bpy.path.display_name_from_filepath(facepath)+'.bin'
        row=box.row(align=0)
        if facepath[-4:] != '.bin':
            row.enabled=0
        row.operator("face.operator",text="Import Trophy").face_opname="import_face"
        row.operator("face.operator",text="Export Trophy").face_opname="export_face"
        row=box.row(align=0)
        
        if obj:
            if bpy.context.mode != 'OBJECT':
                for i in range(3):
                    row = layout.row()
                if obj.name[:14] == 'PES_PS2_Trophy':
                    vco=scn.statistics().split('Verts:')[1][:8].split('/')[1][:3]
                    if vco == str(scn.face_vc):
                        box=layout.box()
                        box.label(text="Trophy Base Model Vertex Count = "+str(scn.face_vc),icon='INFO')     
                    else:
                        box=layout.box()
                        box.label(text="Vertex Count is Not Equal with Trophy Base Model !!",icon='ERROR')
                    
        #for i in range(4):
        #    row = layout.row()        
        #for i in range(7):
        #    row = layout.row()
        box=layout.box()
        box.label(tool_id,icon="INFO")
        box.label("Made by PES Indie Team",icon="INFO")
        box.operator("wm.url_open",text="Go to Evo-Web Official Thread",icon="URL").url="https://evoweb.uk/threads/pes-we-jl-blender-2-67-trophy-modifier-add-on.91969/"
        for i in range(5):
            row = layout.row()
        
class Trophy_Modifier_OP(bpy.types.Operator):
    
    bl_idname = "face.operator"
    bl_label = "Add Trophy"
    
    face_opname = StringProperty()
    
    @classmethod
    def poll(cls, context):
        return context.mode=="OBJECT"
    
    def execute(self, context):
        
        global facepath,face_id
        scn=bpy.context.scene
        
        if self.face_opname=="import_face":
            if os.access(facepath,0) == 1 and facepath[-4:] == '.bin':
                model="face"
                if scn.pes_ver == "pes_ps2":
                    pes_ps2_imp(self, context, model)    
                    return {'FINISHED'}
            else:
                print("")
                self.report( {"ERROR"}, " File Not Found: No Selected File, Wrong Filepath or File does not Exist !!" )
                return {'FINISHED'}
        
        elif self.face_opname=="export_face":
            model='face'
            if scn.pes_ver == "pes_ps2":
                run=pes_ps2_exp(self,model)
                str=" "
            if run:
                print("")
                self.report( {"INFO"}, " Trophy Model"+str+"Exported Successfully..." )
                print(tool_id)
                print("Made by PES Indie Team")
                print("")
                return {'FINISHED'}
            else:
                print("")
                return {'FINISHED'}
                     

def register():
    bpy.utils.register_module(__name__)
    pass

def unregister():
    bpy.utils.unregister_module(__name__)
    pass

if __name__ == "__main__":
    register()
 