import imath
import alembic
from alembic import AbcGeom, Abc
import numpy as np
import os

import obj
import meshsmooth

KWrapExisting = alembic.Abc.WrapExistingFlag.kWrapExisting

def walk_objects(obj, meshs):
    if AbcGeom.IPolyMesh.matches(obj.getHeader()):
        meshs.append(AbcGeom.IPolyMesh(obj, KWrapExisting))

    for i in range(obj.getNumChildren()):
        child = obj.getChild(i)
        walk_objects(child, meshs)

abc_file = os.path.join(os.path.dirname(__file__) , "monkey.abc")

archive = alembic.Abc.IArchive(abc_file)
mesh_list = []
walk_objects(archive.getTop(), mesh_list)

mesh = mesh_list[0]
schema = mesh.getSchema()
secs = 0.0
sel = Abc.ISampleSelector(secs)
meshsamp = schema.getValue(sel)

n = schema.getNormalsParam()
uv = schema.getUVsParam()

uvsamp = uv.getIndexedValue()
normalsamp = n.getIndexedValue()


face_counts = np.array(meshsamp.getFaceCounts(), dtype=np.int32)
face_indices = np.array(meshsamp.getFaceIndices(), dtype=np.int32)
vertices = np.array([ (v[0], v[1], v[2]) for v in meshsamp.getPositions()], dtype=np.float32)

print normalsamp.isIndexed()
print uvsamp.isIndexed()

# normal_values = np.array([(item[], item[1], item[2]) for item in normalsamp.getVals()], dtype=np.float32)
normal_values = np.array(normalsamp.getVals(), dtype=np.float32)
normal_indices = np.array(normalsamp.getIndices(), dtype=np.int32)



channels = [meshsmooth.FVarChannel("uvs", np.array(uvsamp.getIndices(), dtype=np.int32),
                                    np.array(uvsamp.getVals(), dtype=np.float32)),
            meshsmooth.FVarChannel("normals", normal_indices,
                                           normal_values),
         ]
#                         ]
vertice_channel = meshsmooth.FVarChannel("verts", face_indices, vertices)
mesh = meshsmooth.Mesh(face_counts, vertice_channel,channels)

refiner = meshsmooth.TopologyRefiner(mesh)
level = 2
# refiner.refine_uniform(level)
m = refiner.refine_uniform(level)

# print np.array(m.vertices)
# print np.array(m.face_counts)
# print np.array(m.fvchannels[1].values)

out_obj = obj.Obj()

out_obj.vertices = np.array(m.vertices.values)
out_obj.normals = np.array(m.fvchannels[1].values)
out_obj.uvs = np.array(m.fvchannels[0].values)

out_obj.face_sizes = np.array(m.face_counts)
out_obj.face_indices = np.array(m.vertices.indices)
out_obj.normal_indices = np.array(m.fvchannels[1].indices)
out_obj.uv_indices = np.array(m.fvchannels[0].indices)

out_obj.write(os.path.join(os.path.dirname(__file__) , "monekeyabc_smooth.obj"), True)
