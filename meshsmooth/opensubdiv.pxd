cdef extern from "opensubdiv/far/topologyDescriptor.h" namespace "OpenSubdiv::Far" nogil:
    cdef cppclass TopologyLevel:
        int GetNumVertices()
        int GetNumFaces()
        int GetNumFaceVertices()
        int GetNumFVarValues(int channel)

    cdef cppclass TopologyRefiner:
        int GetNumVerticesTotal()
        int GetNumFVarValuesTotal(int channel)
        int GetMaxLevel()
        TopologyLevel& GetLevel(int level)

    cdef cppclass TopologyDescriptor:
        TopologyDescriptor()
        int numVertices
        int numFaces
        int *numVertsPerFace
        int *vertIndicesPerFace;
        cppclass FVarChannel:
            FVarChannel()
            int numValues
            int *valueIndices
        int numFVarChannels
        FVarChannel *fvarChannels

cdef extern from "opensubdiv/far/topologyDescriptor.h" namespace "OpenSubdiv::Far::TopologyRefiner" nogil:
    cdef cppclass UniformOptions:
        UniformOptions(int level)

cdef extern from "opensubdiv/far/primvarRefiner.h" namespace "OpenSubdiv::Far" nogil:
    cdef cppclass PrimvarRefiner:
        pass