#include <opensubdiv/far/topologyDescriptor.h>
#include <opensubdiv/far/primvarRefiner.h>
#include "stdint.h"
#include <vector>

using namespace OpenSubdiv;
typedef Far::TopologyDescriptor Descriptor;

struct FVarData {
    int *indices;
    float *values;
    int indice_size;
    int channel_id;
    int value_shape[2];
};

struct SubdiveDesc
{
    int level;
    int *dst_face_counts;
    FVarData src_vertices;
    FVarData dst_vertices;
    uint8_t * coarse_levels;
    std::vector<FVarData> src_fvar;
    std::vector<FVarData> dst_fvar;
};

Far::TopologyRefiner * create_refiner(Descriptor &desc,
                                      Sdc::Options::VtxBoundaryInterpolation VtxBoundaryInterpolation,
                                      Sdc::Options::FVarLinearInterpolation FVarLinearInterpolation);
void refine_uniform(Far::TopologyRefiner *refiner, int level);
void populate_indices(Far::TopologyRefiner *refiner, SubdiveDesc &desc);
void populate_coarse_edge_levels(Far::TopologyRefiner *refiner, SubdiveDesc &desc);
void subdivide_uniform(Far::TopologyRefiner *refiner, SubdiveDesc &desc);
