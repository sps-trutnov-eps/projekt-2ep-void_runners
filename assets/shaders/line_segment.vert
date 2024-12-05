#version 330

// a minimal billboard vertex shader for line segments

layout(std140) uniform cue_camera_buf {
    mat4 bt_cam_mat;
};

uniform vec3 cam_pos[64];
uniform float line_width[64];

in vec3 pos;
in vec3 norm; // points *along* the line segment
in vec2 uv;

out vec3 frag_pos; // world space
out vec3 frag_norm;
out vec2 frag_uv;

flat out int frag_ins_id;

void main() {
    // find dir along which to extend the billboard
    // vec3 d_proj = ((cam_pos[gl_InstanceID] - pos) * norm) / (norm * norm);
    vec3 quad_dir = normalize(cross(cam_pos[gl_InstanceID] - pos, norm));

    // extend by line width
    vec4 w_pos = vec4(pos + quad_dir * line_width[gl_InstanceID] *  (1. - 2 * (gl_VertexID % 2)), 1.);
    gl_Position = bt_cam_mat * w_pos;

    // pass to fragment shader interpolators
    frag_pos = w_pos.xyz;
    frag_norm = (vec4(norm, 0.)).xyz;
    frag_norm = quad_dir;
    frag_uv = uv;
    frag_ins_id = gl_InstanceID;
}
