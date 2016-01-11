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
vertices = np.array(meshsamp.getPositions(), dtype=np.float32)

normals = np.array(normalsamp.getVals(), dtype=np.float32)

print len(vertices)
print len(normals)
print len(face_indices)
#for item in np.array(normalsamp.getIndices(), dtype=np.int32):
#    print item


out_obj = obj.Obj()

out_obj.vertices = vertices
out_obj.normals = np.array([(item[0], item[1], item[2]) for item in normalsamp.getVals()], dtype=np.float32)
out_obj.uvs = np.array(uvsamp.getVals(), dtype=np.float32)

out_obj.face_sizes = face_counts
indices = []

out_obj.face_indices = face_indices
# out_obj.normal_indices = np.array(m.fvchannels[1].indices)
out_obj.normal_indices = np.array(normalsamp.getIndices(), dtype=np.int32)
out_obj.uv_indices = np.array(uvsamp.getIndices(), dtype=np.int32)

out_obj.write(os.path.join(os.path.dirname(__file__) , "monekeyabc_convert.obj"), True)
