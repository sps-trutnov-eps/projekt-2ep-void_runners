#version 330

in vec2 frag_uv;
in vec3 frag_norm;
out vec4 frag;

uniform sampler2D albedo;

void main() {
    // frag = vec4(frag_norm, 1.); 
    frag = texture(albedo, frag_uv);
}