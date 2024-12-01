#version 330

// a basic mesh vertex shader with no special effects

layout(std140) uniform cue_camera_buf {
    mat4 bt_cam_mat;
};

uniform mat4 cue_model_mat[256];

in vec3 pos;
in vec3 norm;
in vec2 uv;

out vec3 frag_pos; // world space
out vec3 frag_norm;
out vec2 frag_uv;

flat out int frag_ins_id;

void main() {
    vec4 w_pos = cue_model_mat[gl_InstanceID] * vec4(pos, 1.);
    gl_Position = bt_cam_mat * w_pos;

    // pass to fragment shader interpolators
    frag_pos = w_pos.xyz;
    frag_norm = (cue_model_mat[gl_InstanceID] * vec4(norm, 0.)).xyz;
    frag_uv = uv;
    frag_ins_id = gl_InstanceID;
}
