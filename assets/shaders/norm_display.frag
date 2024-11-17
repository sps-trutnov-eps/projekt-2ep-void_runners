#version 330

in vec2 frag_uv;
in vec3 frag_norm;
out vec4 frag;

void main() {
    frag = vec4(frag_norm, 1.); 
}