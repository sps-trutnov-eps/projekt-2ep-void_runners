#version 330

in vec2 frag_uv;
out vec4 frag;

uniform sampler2D in_tex;

void main() {
    frag = texture(in_tex, frag_uv);
}