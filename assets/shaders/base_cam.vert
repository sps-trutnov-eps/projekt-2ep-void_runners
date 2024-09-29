#version 330

// a basic mesh vertex shader with no special effects

layout(std140) uniform cue_camera_buf {
    mat4 bt_cam_mat;
};

uniform mat4 cue_model_mat;

in vec3 pos;
in vec3 norm;
in vec2 uv;

out vec3 frag_pos; // world space
out vec3 frag_norm;
out vec2 frag_uv;

void main() {
    vec4 w_pos = cue_model_mat * vec4(pos, 1.);
    gl_Position = bt_cam_mat * w_pos;

    // pass to fragment shader interpolators
    frag_pos = w_pos.xyz;
    frag_col = norm;
    frag_uv = uv;
}
