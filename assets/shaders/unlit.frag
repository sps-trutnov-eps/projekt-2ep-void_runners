#version 330

in vec2 frag_uv;
in vec3 frag_norm;
out vec4 frag;

uniform sampler2D albedo;

void main() {
    frag = texture(albedo, frag_uv); // * vec4(vec3(.2), 1.);
}