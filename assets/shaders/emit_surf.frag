#version 330

in vec2 frag_uv;
in vec3 frag_norm;
out vec4 frag;

uniform sampler2D albedo;
uniform float emit_power;

void main() {
    frag = texture(albedo, frag_uv) * vec4(emit_power, emit_power, emit_power, 1.);
}