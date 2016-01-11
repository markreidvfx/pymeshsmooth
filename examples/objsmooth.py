import os
import obj
import meshsmooth
import numpy as np

test_obj_path = os.path.join(os.path.dirname(__file__) , "monkey.obj")
o = obj.Obj()

o.open(test_obj_path)


#varying_channels = [VarChannel("color", color )]
channels = [meshsmooth.FVarChannel("uvs", o.uv_indices, o.uvs),
            meshsmooth.FVarChannel("normals", o.normal_indices, o.normals),
            ]

vertice_chan = meshsmooth.FVarChannel("verts", o.face_indices, o.vertices)

mesh = meshsmooth.Mesh(o.face_sizes, vertice_chan, channels)

refiner = meshsmooth.TopologyRefiner(mesh)
level = 2

m = refiner.refine_uniform(level)

print np.array(m.vertices)
print np.array(m.face_counts)
print np.array(m.fvchannels[1].values)


out_obj = obj.Obj()

out_obj.vertices = np.array(m.vertices.values)
out_obj.normals = np.array(m.fvchannels[1].values)
out_obj.uvs = np.array(m.fvchannels[0].values)

out_obj.face_sizes = np.array(m.face_counts)
out_obj.face_indices = np.array(m.vertices.indices)
out_obj.normal_indices = np.array(m.fvchannels[1].indices)
out_obj.uv_indices = np.array(m.fvchannels[0].indices)

# for item in out_obj.uv_indices:
#    print out_obj.uvs[item]


out_obj.write(os.path.join(os.path.dirname(__file__) , "monekey_smooth.obj"))
