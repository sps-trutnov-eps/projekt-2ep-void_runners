#version 330

flat in int frag_ins_id;
in vec2 frag_uv;
in vec3 frag_norm;
out vec4 frag;

uniform sampler2D albedo;
uniform float emit_power[256];

void main() {
    frag = texture(albedo, frag_uv) * vec4(emit_power[frag_ins_id], emit_power[frag_ins_id], emit_power[frag_ins_id], 1.);
}