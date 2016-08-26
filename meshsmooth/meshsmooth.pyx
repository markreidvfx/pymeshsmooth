from libcpp.vector cimport vector
from cython cimport view

cimport opensubdiv

cdef extern from "core.h" namespace "OpenSubdiv::Sdc::Options" nogil:
    cdef enum VtxBoundaryInterpolation:
        VTX_BOUNDARY_NONE
        VTX_BOUNDARY_EDGE_ONLY
        VTX_BOUNDARY_EDGE_AND_CORNER

    cdef enum FVarLinearInterpolation:
        FVAR_LINEAR_NONE
        FVAR_LINEAR_CORNERS_ONLY
        FVAR_LINEAR_CORNERS_PLUS1
        FVAR_LINEAR_CORNERS_PLUS2
        FVAR_LINEAR_BOUNDARIES
        FVAR_LINEAR_ALL

cdef extern from "core.h" nogil:
    cdef struct FVarData:
        int *indices
        float *values
        int indice_size
        int channel_id
        int value_shape[2]

    cdef struct SubdiveDesc:
        int level
        int *dst_face_counts
        FVarData src_vertices
        FVarData dst_vertices;
        vector[FVarData] src_fvar
        vector[FVarData] dst_fvar

    cdef opensubdiv.TopologyRefiner* create_refiner(opensubdiv.TopologyDescriptor &desc, VtxBoundaryInterpolation, FVarLinearInterpolation) except+
    cdef void refine_uniform(opensubdiv.TopologyRefiner* refiner, int level) except+
    cdef void populate_indices(opensubdiv.TopologyRefiner *refiner, SubdiveDesc &desc) except+
    cdef void subdivide_uniform(opensubdiv.TopologyRefiner *refiner, SubdiveDesc &desc) except+

cdef dict Vtx_Boundary_Interpolation = {
"NONE":            VTX_BOUNDARY_NONE,
"EDGE_ONLY":       VTX_BOUNDARY_EDGE_ONLY,
"EDGE_AND_CORNER": VTX_BOUNDARY_EDGE_AND_CORNER,
}

cdef dict F_Var_Linear_Interpolation = {
"LINEAR_NONE":          FVAR_LINEAR_NONE,
"LINEAR_CORNERS_ONLY":  FVAR_LINEAR_CORNERS_ONLY,
"LINEAR_CORNERS_PLUS1": FVAR_LINEAR_CORNERS_PLUS1,
"LINEAR_CORNERS_PLUS2": FVAR_LINEAR_CORNERS_PLUS2,
"LINEAR_BOUNDARIES":    FVAR_LINEAR_BOUNDARIES,
"LINEAR_ALL":           FVAR_LINEAR_ALL,
}


cdef class Channel(object):
    cdef public float[:,:] values

    def __cinit__(self):
        self.values = None

cdef class VarChannel(Channel):
    def __init__(self, str name, float[:,:] values not None):
        self.values = values

cdef class FVarChannel(Channel):
    cdef public int[:] indices
    cdef int channel_id

    def __cinit__(self):
        self.indices = None

    def __init__(self, str name,
                       int[:] indices not None,
                       float[:,:] values not None):

            self.indices = indices
            self.values = values

    cdef FVarData get_description(self):
        cdef FVarData d;
        d.indices = &self.indices[0]
        d.values = &self.values[0][0]
        d.indice_size = len(self.indices)
        d.channel_id = self.channel_id
        d.value_shape[0] = self.values.shape[0]
        d.value_shape[1] = self.values.shape[1]
        return d


cdef class Mesh(object):
    cdef public int[:] face_counts
    cdef public FVarChannel vertices
    cdef public list vchannels
    cdef public list fvchannels

    def __cinit__(self):
        self.face_counts = None

    def __init__(self, int[:] face_counts not None,
                       FVarChannel vertex_channel not None,
                           channels):

        self.face_counts = face_counts
        self.vertices = vertex_channel
        self.vchannels = []
        self.fvchannels = []
        for channel in channels:
            if isinstance(channel, FVarChannel):
                self.fvchannels.append(channel)
            elif isinstance(channel, VarChannel):
                self.vchannels.append(channel)
            else:
                raise TypeError("unkown channel type")

cdef class TopologyRefiner(object):
    cdef opensubdiv.TopologyRefiner *refiner
    cdef opensubdiv.TopologyDescriptor desc
    cdef vector[opensubdiv.TopologyDescriptor.FVarChannel] fvar_descriptors
    cdef public Mesh mesh

    def __cinit__(self):
        self.refiner = NULL
    def __dealloc__(self):
        if self.refiner:
            del self.refiner

    def __init__(self, Mesh mesh not None, BoundaryInterpolation=None, FVarInterpolation=None):

        cdef FVarChannel fvchan

        self.mesh = mesh

        self.desc.numVertices = self.mesh.vertices.values.shape[0]
        self.desc.numFaces = self.mesh.face_counts.shape[0]
        self.desc.numVertsPerFace = &self.mesh.face_counts[0]
        self.desc.vertIndicesPerFace = &self.mesh.vertices.indices[0]

        self.fvar_descriptors.resize(len(self.mesh.fvchannels))

        for i, fvchan in enumerate(self.mesh.fvchannels):
            fvchan.channel_id = i
            self.fvar_descriptors[i].numValues = fvchan.indices.shape[0]
            self.fvar_descriptors[i].valueIndices = &fvchan.indices[0]

        self.desc.numFVarChannels = self.fvar_descriptors.size()
        self.desc.fvarChannels = &self.fvar_descriptors[0]

        cdef VtxBoundaryInterpolation boundry_interp = VTX_BOUNDARY_EDGE_ONLY
        cdef FVarLinearInterpolation fvar_interp= FVAR_LINEAR_BOUNDARIES
        if BoundaryInterpolation:
            boundry_interp = Vtx_Boundary_Interpolation[BoundaryInterpolation.upper()]

        if FVarInterpolation:
            fvar_interp = F_Var_Linear_Interpolation[FVarInterpolation.upper()]

        with nogil:
            self.refiner = create_refiner(self.desc, boundry_interp, fvar_interp)

    cdef setup_dst_mesh(self, int level, Mesh mesh=None):
        """
        setups a mesh, attempts to reuse one if provided
        """
        cdef FVarChannel dst_fvchan
        cdef FVarChannel src_fvchan

        if not mesh:
            mesh = Mesh.__new__(Mesh)
            mesh.face_counts = None
            mesh.vertices = None

        vert_count = self.refiner.GetLevel(level).GetNumVertices()
        face_count = self.refiner.GetLevel(level).GetNumFaces()
        indice_count = self.refiner.GetLevel(level).GetNumFaceVertices()

        if mesh.face_counts is None or mesh.face_counts.shape[0] != face_count:
            mesh.face_counts = view.array(shape=(face_count, ), itemsize=sizeof(int), format="i")

        if mesh.vertices is None:
            mesh.vertices =  FVarChannel.__new__(FVarChannel)

        if mesh.vertices.indices is None or mesh.vertices.indices.shape[0] != indice_count:
            mesh.vertices.indices = view.array(shape=(indice_count, ), itemsize=sizeof(int), format="i")

        vertex_element_size = self.mesh.vertices.values.shape[1]

        if mesh.vertices.values is None or mesh.vertices.values.shape != (vert_count, vertex_element_size):
            mesh.vertices.values = view.array(shape=(vert_count, vertex_element_size), itemsize=sizeof(float), format="f")

        has_channels = True
        if mesh.fvchannels is None:
            mesh.fvchannels = []
            has_channels = False

        for i, src_fvchan in enumerate(self.mesh.fvchannels):

            if has_channels and len(mesh.fvchannels) > i:
                dst_fvchan = mesh.fvchannels[i]
            else:
                dst_fvchan =  FVarChannel.__new__(FVarChannel)

            dst_fvchan.channel_id = src_fvchan.channel_id

            if dst_fvchan.indices is None or dst_fvchan.indices.shape[0] != indice_count:
                dst_fvchan.indices = view.array(shape=(indice_count, ), itemsize=sizeof(int), format="i")

            elements = src_fvchan.values.shape[1]
            size = self.refiner.GetLevel(level).GetNumFVarValues(i)

            if dst_fvchan.values is None or dst_fvchan.values.shape != (size, elements):
                dst_fvchan.values = view.array(shape=(size, elements), itemsize=sizeof(float), format="f")

            if not (has_channels and len(mesh.fvchannels) > i):
                mesh.fvchannels.append(dst_fvchan)

        return mesh

    cdef void setup_subdiv_descriptor(self, int level, SubdiveDesc &desc, Mesh dst_mesh):
        cdef FVarChannel src_fvchan
        cdef FVarChannel dst_fvchan

        channel_count = len(self.mesh.fvchannels)
        desc.src_fvar.resize(channel_count)
        desc.dst_fvar.resize(channel_count)

        desc.level = level
        desc.dst_face_counts = &dst_mesh.face_counts[0]
        desc.dst_vertices = dst_mesh.vertices.get_description()
        desc.src_vertices = self.mesh.vertices.get_description()

        for i in range(channel_count):
            src_fvchan = self.mesh.fvchannels[i]
            dst_fvchan = dst_mesh.fvchannels[i]
            desc.src_fvar[i] = src_fvchan.get_description()
            desc.dst_fvar[i] = dst_fvchan.get_description()

    def refine_uniform(self, int level, Mesh mesh = None, generate_indices = True):

        if level != self.refiner.GetMaxLevel():
            with nogil:
                refine_uniform(self.refiner, level)

        mesh = self.setup_dst_mesh(level, mesh)

        cdef SubdiveDesc desc
        self.setup_subdiv_descriptor(level, desc, mesh)

        with nogil:
            subdivide_uniform(self.refiner, desc)

        if generate_indices:
            with nogil:
                populate_indices(self.refiner, desc)
        return mesh
