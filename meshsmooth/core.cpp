#include "core.h"
#include <iostream>

struct Vertex2D {
    void Clear() {values[0] = values[1] = 0; }
    void AddWithWeight(Vertex2D const & src, float weight)
    {
        values[0] += weight * src.values[0];
        values[1] += weight * src.values[1];
    }
    float values[2];
};

struct Vertex3D {
    void Clear() {values[0] = values[1] = values[2] = 0; }
    void AddWithWeight(Vertex3D const & src, float weight)
    {
		values[0] += weight * src.values[0];
		values[1] += weight * src.values[1];
		values[2] += weight * src.values[2];
    }
    float values[3];
};

struct Vertex4D {
    void Clear() {values[0] = values[1] = values[2] = values[3] = 0; }
    void AddWithWeight(Vertex4D const & src, float weight)
    {
		values[0] += weight * src.values[0];
		values[1] += weight * src.values[1];
		values[2] += weight * src.values[2];
		values[3] += weight * src.values[3];
    }
    float values[4];
};


Far::TopologyRefiner * create_refiner(Descriptor &desc,
                                      Sdc::Options::VtxBoundaryInterpolation VtxBoundaryInterpolation,
                                      Sdc::Options::FVarLinearInterpolation FVarLinearInterpolation)
{
    OpenSubdiv::Sdc::SchemeType type = OpenSubdiv::Sdc::SCHEME_CATMARK;
    OpenSubdiv::Sdc::Options options;
    options.SetVtxBoundaryInterpolation(VtxBoundaryInterpolation);
    //options.SetFVarLinearInterpolation(Sdc::Options::FVAR_LINEAR_CORNERS_PLUS2);
    options.SetFVarLinearInterpolation(FVarLinearInterpolation);

    return Far::TopologyRefinerFactory<Descriptor>::Create(desc,
                    Far::TopologyRefinerFactory<Descriptor>::Options(type,options));
}

void refine_uniform(Far::TopologyRefiner *refiner, int level)
{
    Far::TopologyRefiner::UniformOptions refineOptions(level);
    refineOptions.fullTopologyInLastLevel = true;
    refiner->RefineUniform(refineOptions);

}

void walk_child_edges(Far::Index edge_index,
                      Far::TopologyRefiner *refiner,
                      uint8_t * result,
                      int current_level,
                      int final_level)
{
    Far::TopologyLevel const &level = refiner->GetLevel(current_level);

    if (current_level == final_level) {
        Far::ConstIndexArray vert_indices = level.GetEdgeVertices(edge_index);
        for (int i = 0; i < vert_indices.size(); i++) {
            result[vert_indices[i]] = 0;
        }
        return;
    }

    Far::ConstIndexArray edges = level.GetEdgeChildEdges(edge_index);

    for (int i = 0; i < edges.size(); i++) {
        walk_child_edges(edges[i], refiner, result, current_level+1, final_level);
    }

}

void populate_coarse_edge_levels(Far::TopologyRefiner *refiner, SubdiveDesc &desc)
{
    int final_level = desc.level;
    uint8_t *result = desc.coarse_levels;

    memset(result, final_level, refiner->GetLevel(final_level).GetNumVertices());
    Far::TopologyLevel const &first_level = refiner->GetLevel(0);

    for (int e = 0; e < first_level.GetNumEdges(); e++) {
        walk_child_edges(e, refiner, result, 0, final_level);
    }
}

void populate_indices(Far::TopologyRefiner *refiner, SubdiveDesc &desc)
{
	int level = desc.level;
	Far::TopologyLevel const & last_level = refiner->GetLevel(level);
	int channel_count = desc.dst_fvar.size();
	int face_count = last_level.GetNumFaces();
	int face_index = 0;

	for (int face = 0; face < face_count; ++face) {
		Far::ConstIndexArray fverts = last_level.GetFaceVertices(face);

		int start_index = face_index;

		desc.dst_face_counts[face] = fverts.size();
		for (int i = 0; i <  fverts.size(); i++) {
			desc.dst_vertices.indices[face_index] = fverts[i];
			face_index++;
		}

		for (int i = 0; i < channel_count; i++) {
			FVarData &dst_fvar_desc = desc.dst_fvar[i];
			int channel = dst_fvar_desc.channel_id ;
			Far::ConstIndexArray values = last_level.GetFaceFVarValues(face, channel);
			face_index = start_index;
			for (int i = 0; i <  values.size(); i++) {
				dst_fvar_desc.indices[face_index] = values[i];
				face_index++;
			}
		}
		face_index = start_index + fverts.size();
	}

}

void subdivide_uniform(Far::TopologyRefiner *refiner, SubdiveDesc &desc)
{
	int maxlevel = desc.level;
	int coarse_verts = desc.src_vertices.value_shape[0];
	int fine_verts   = refiner->GetLevel(maxlevel).GetNumVertices();
	int total_verts  = refiner->GetNumVerticesTotal();
	int temp_verts   = total_verts - coarse_verts - fine_verts;

	int vertex_element_size = desc.src_vertices.value_shape[1];

	std::vector<float> tmp_vertices(temp_verts*vertex_element_size);

	float *src_vertices = (float*)desc.src_vertices.values;
	float *dst_vertices = (float*)&tmp_vertices[0];

	int channel_count = desc.src_fvar.size();
	std::vector<std::vector<float> > tmp_fvars(channel_count);
	std::vector<float*> src_fvars(channel_count);
	std::vector<float*> dst_fvars(channel_count);

	for (int i = 0; i < channel_count; i++) {
		FVarData &src_fvar_desc = desc.src_fvar[i];
		FVarData &dst_fvar_desc = desc.dst_fvar[i];
		int channel = src_fvar_desc.channel_id;
		int coarse_size = src_fvar_desc.value_shape[0];
		int fine_size = dst_fvar_desc.value_shape[0];
		int total_size = refiner->GetNumFVarValuesTotal(channel);
		int temp_size = total_size;// - coarse_size - fine_size;

		int element_size = src_fvar_desc.value_shape[1];

		tmp_fvars[i].resize(temp_size * element_size);

		src_fvars[i] = src_fvar_desc.values;
		dst_fvars[i] = &tmp_fvars[i][0];
	}

	OpenSubdiv::Far::PrimvarRefiner primvarRefiner(*refiner);
	for (int level = 1; level <= maxlevel; ++level) {

		if (level ==  maxlevel) {
			dst_vertices = (float*)desc.dst_vertices.values;
		}

		if (vertex_element_size == 3) {
			Vertex3D* src = (Vertex3D*)src_vertices;
			Vertex3D* dst = (Vertex3D*)dst_vertices;
			primvarRefiner.Interpolate(level, src, dst);

		} else if (vertex_element_size == 4) {
			Vertex4D* src = (Vertex4D*)src_vertices;
			Vertex4D* dst = (Vertex4D*)dst_vertices;
			primvarRefiner.Interpolate(level, src, dst);
		}

		src_vertices = dst_vertices;
		dst_vertices += refiner->GetLevel(level).GetNumVertices() * vertex_element_size;

		for (int i = 0; i < channel_count; i++) {
			FVarData &src_fvar_desc = desc.src_fvar[i];
			FVarData &dst_fvar_desc = desc.dst_fvar[i];
			int element_size = src_fvar_desc.value_shape[1];
			int channel = src_fvar_desc.channel_id;

			if (level ==  maxlevel) {
				dst_fvars[i] = dst_fvar_desc.values;
			}

			if ( element_size == 2) {
				Vertex2D* src = (Vertex2D*)src_fvars[i];
				Vertex2D* dst = (Vertex2D*)dst_fvars[i];
				primvarRefiner.InterpolateFaceVarying(level, src, dst, channel);
			} else if ( element_size == 3) {
				Vertex3D* src = (Vertex3D*)src_fvars[i];
				Vertex3D* dst = (Vertex3D*)dst_fvars[i];
				primvarRefiner.InterpolateFaceVarying(level, src, dst, channel);
			} else {
				continue;
			}

			src_fvars[i] = dst_fvars[i];
			dst_fvars[i] += (refiner->GetLevel(level).GetNumFVarValues(channel) * element_size);
		}

	}

}
