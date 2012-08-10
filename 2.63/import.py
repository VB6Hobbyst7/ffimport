import bpy
import struct

def load_p(filepath, debug, wireframe):
    f = open(filepath, 'rb')

    header = f.read(64)
    runtimeData = f.read(64) # usually not read, but may be used in export.
    header = struct.unpack('llllllllllllllll', header) # convert binary header to integers

    #Break the header into variables
    version = header[0]
    vertexType = header[2]
    numVertices = header[3]
    numNormals = header[4]
    numUnknown1 = header[5]
    numTexCoords = header[6]
    numVertexColors = header[7]
    numEdges = header[8]
    numUnknown2 = header[10]
    numUnknown3 = header[11]
    numPolygons = header[9]
    numHundreds = header[12]
    numGroups = header[13]
    numBoundingBoxes = header[14]
    normIndexTableFlag = header[15]

    if debug == True:
        print('Verticies: \t', numVertices)
        print('Edges: \t\t', numEdges)
        print('Faces: \t\t', numPolygons)
        print('NumUnknown: \t', numUnknown1)

    # Loaded in all the parts of the file. Taken from code posted by Aali :)
    vertices =   [list(struct.unpack("fff",                       f.read(0xC)))  for i in range(numVertices)]
    normals =    [struct.unpack("fff",                       f.read(0xC))  for i in range(numNormals)]
    unknown1 =   [struct.unpack("fff",                       f.read(0xC))  for i in range(numUnknown1)]
    texcoords =  [struct.unpack("ff",                        f.read(0x8))  for i in range(numTexCoords)]
    vertcolors = [struct.unpack("I",                         f.read(0x4))  for i in range(numVertexColors)]
    polycolors = [struct.unpack("I",                         f.read(0x4))  for i in range(numPolygons)]
    edges =      [list(struct.unpack("hh",                         f.read(0x4)))  for i in range(numEdges)]
    polygonsTmp =   [struct.unpack("HHHHHHHHHHI",               f.read(0x18)) for i in range(numPolygons)]
    unknown2 =   [struct.unpack("HHHHHHHHHHI",               f.read(0x18)) for i in range(numUnknown2)]
    unknown3 =   [struct.unpack("BBB",                       f.read(0x3))  for i in range(numUnknown3)]
    hundreds =   [struct.unpack("IIIIIIIIIIIIIIIIIIIIIIIII", f.read(0x64)) for i in range(numHundreds)]
    groups =     [struct.unpack("IIIIIIIIIIIIII",            f.read(0x38)) for i in range(numGroups)]
    boundingboxes = [struct.unpack("IIIIIII",                   f.read(0x1C)) for i in range(numBoundingBoxes)]    

    polygons = []

    for i in range(len(polygonsTmp)):
        polygons.append([polygonsTmp[i][1], polygonsTmp[i][2], polygonsTmp[i][3]])

    # Load Faces
    #polys = []
    #for i in range(numPolygons):
    #    poly = list(struct.unpack('hhhhhhhhhhl', f.read(24)))
    #    poly = [poly[1], poly[2], poly[3]]
    #    if debug == True:
    #        print(poly)
    #    polys.append(poly)

    #parse da groups ze correct way
    for i, group in enumerate(groups):
        print('\n\nLoading group:\n')
        print(group)
        polyOffset = group[1]
        polyRange = group[2]
        vertexOffset = group[3]
        vertexRange = group[4]
        edgeOffset = group[5]
        edgeRange = group[6]

        textureOffset = group[11]
        isTextured = bool(group[12])

        if debug == True:
            print('Vertex Offset: \t', vertexOffset)
            print('Vertex Range: \t', vertexRange)
            print('Edge Offset: \t', edgeOffset)
            print('Edge Range: \t', edgeRange)
            print('Polygon Offset: ', polyOffset)
            print('Poly Range: \t', polyRange)
            print('Textured: \t', isTextured)
            print('Texture Offset: ', textureOffset, '\n')

        #generate verts and faces for this group
        groupVertices = vertices[vertexOffset:(vertexRange + vertexOffset)]
        groupEdges = edges[edgeOffset: (edgeRange + edgeOffset)]
        groupPolygons = polygons[polyOffset : (polyRange+ polyOffset)]
        print(groupVertices)
        print('\n', groupPolygons)

        print('adding to from_pydata')
        ffMesh = bpy.data.meshes.new('ffimport' + str(i))
        ffMesh.from_pydata(groupVertices, [], groupPolygons)
        print('tring to update')
        ffMesh.update()
        ffObject = bpy.data.objects.new('ffimport' + str(i), ffMesh)
        bpy.context.scene.objects.link(ffObject)
        print('success!')


    if wireframe == True:
        create_mesh('ffimport', vertices, edges)
#    else:
#        create_mesh('ffimport', vertices, [], polys)


    # load materials

    #step 1: enumerate materials
#        for i in range(num)

    f.close()

def start_import(context, filepath, debug, wireframe):
    #first thing first is to determin the type of file we are working with
    filepath = filepath.replace('\\', '/')
    filename = filepath.split('/')[-1]
    filetype = filename.split('.')[-1]

    if debug == True:
        print(filename)
        print(filetype)

    #which ever filetype we are using, call the appropriate function
    if filetype == 'p':
        load_p(filepath, debug, wireframe)

    return {'FINISHED'}


# ImportHelper is a helper class, defines filename and
# invoke() function which calls the file selector.
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator



#main class to setup import window for blender
class ffimport(Operator, ImportHelper):
    '''Import Final Fatnasy files (.hrc .rsd .p .tex .a)'''
    bl_idname = "import_test.some_data"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Import"

    filename_ext = ".p" #Not quite sure how blender uses this

    filter_glob = StringProperty(
            default="*.p;*.hrc;*.tex;*.rsd;*.a", # Took a while to find, but use a ; to seperate file types :)
            options={'HIDDEN'}
            )

    # Create the User interface 
    debug_s = BoolProperty(name="Debug", description="Toggels debug info sent to the console.", default=True)
    wireframe = BoolProperty(name="Wireframe", description="Loads only vertices and edges", default= False)

    def execute(self, context):
        return start_import(context, self.filepath, self.debug_s, self.wireframe)


# Adds a listing in the Import menu
def menu_func_import(self, context):
    self.layout.operator(ffimport.bl_idname, text="Final Fantasy")


def register():
    bpy.utils.register_class(ffimport)
    bpy.types.INFO_MT_file_import.append(menu_func_import)

def unregister():
    bpy.utils.unregister_class(ffimport)
    bpy.types.INFO_MT_file_import.remove(menu_func_import)

if __name__ == "__main__":
    register()

    # test call
    bpy.ops.import_test.some_data('INVOKE_DEFAULT')
