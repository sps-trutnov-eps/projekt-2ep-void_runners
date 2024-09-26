#version 330

in vec2 frag_uv;
out vec4 frag;

// uniform sampler2D albedo;

void main() {
    frag = vec4(frag_col, 1.);
}