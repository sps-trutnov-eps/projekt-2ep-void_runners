#version 330

// a basic mesh vertex shader for point rendering

layout(std140) uniform cue_camera_buf {
    mat4 bt_cam_mat;
};

in vec3 pos;
in float lifetime;

out vec3 frag_pos; // world space
flat out float frag_lifetime;
flat out int sprite_index;
flat out int frag_ins_id;

void main() {
    vec4 w_pos = vec4(pos, 1.);
    gl_Position = bt_cam_mat * w_pos;
    gl_PointSize = 300 / gl_Position.z;

    frag_lifetime = lifetime;
    sprite_index = int(lifetime);

    // pass to fragment shader interpolators
    frag_pos = w_pos.xyz;
    frag_ins_id = gl_InstanceID;
}
