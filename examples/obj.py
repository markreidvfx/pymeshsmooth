import array
import numpy as np

def group(iterator, count):
    itr = iter(iterator)
    while True:
        yield tuple([itr.next() for i in range(count)])

class Obj(object):

    def __init__(self):
        self.vertices = None
        self.normals = None
        self.uvs = None

        self.face_sizes = None
        self.face_indices = None
        self.normal_indices = None
        self.uv_indices = None

    def open(self, filename):

        normal_indices = []
        uv_indices = []
        face_indices = []
        face_sizes = []

        vertices = []
        normals = []
        uvs = []

        for line in open(filename, "r"):
            if line.startswith('#'): continue
            values = line.split()
            if not values: continue

            if values[0] == 'v':
                v = map(float, values[1:4])
                vertices.extend(v)
                vertices.append(1.0)
            elif values[0] == 'vn':
                v = map(float, values[1:4])
                normals.extend(v)
            elif values[0] == 'vt':
                v = map(float, values[1:3])
                uvs.extend(v)

            elif values[0] == 'f':
                face = []
                uv = []
                norm = []
                for v in values[1:]:
                    w = v.split('/')
                    face.append(int(w[0]) - 1)
                    if len(w) >= 2 and len(w[1]) > 0:
                        uv.append(int(w[1]) - 1)
                    else:
                        uv.append(0)
                    if len(w) >= 3 and len(w[2]) > 0:
                        norm.append(int(w[2]) - 1)
                    else:
                        norm.append(0)

                face_sizes.append(len(face))
                face_indices.extend(face)
                normal_indices.extend(norm)
                uv_indices.extend(uv)

        self.vertices = np.array(vertices, dtype=np.float32)
        self.normals = np.array(normals, dtype=np.float32)
        self.uvs = np.array(uvs, dtype=np.float32)

        self.vertices.shape = (-1, 4)
        self.normals.shape = (-1, 3)
        self.uvs.shape = (-1, 2)


        self.face_sizes = np.array(face_sizes, dtype=np.int32)
        self.face_indices = np.array(face_indices, dtype=np.int32)
        self.normal_indices = np.array(normal_indices, dtype=np.int32)
        self.uv_indices = np.array(uv_indices, dtype=np.int32)

    def write(self, filename, reverse_handedness=False):
        with open(filename, 'w') as f:
            f.write("# OBJ file\n")

            for v in self.vertices:
                f.write("v %.4f %.4f %.4f\n" % tuple(v[:3]))
            for vn in self.normals:
                f.write("vn %.4f %.4f %.4f\n" % tuple(vn))

            for vt in self.uvs:
                f.write("vt %.4f %.4f\n" % tuple(vt))

            i = 0
            for face_size in self.face_sizes:
                f.write("f")

                face_indices = self.face_indices[i:i + face_size]
                uv_indices = self.uv_indices[i:i + face_size]
                normal_indices = self.normal_indices[i:i + face_size]

                if reverse_handedness:
                    face_indices = reversed(face_indices)
                    uv_indices = reversed(uv_indices)
                    normal_indices = reversed(normal_indices)

                for index, uv, normal in zip(face_indices,
                                             uv_indices,
                                             normal_indices):
                    f.write(" %d/%d/%d" % (index + 1, uv + 1, normal + 1))

                f.write("\n")
                i += face_size


#print face, texcoords, norms




if __name__ == "__main__":
    import os
    o = Obj()
    o.open(os.path.join(os.path.dirname(__file__) , "monkey.obj"))
    o.write("test.obj")
