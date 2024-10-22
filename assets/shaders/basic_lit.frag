#version 330

in vec3 frag_norm;
out vec4 frag;

void main() {
    float light_value = dot(frag_norm, -normalize(vec3(-1.2, -1.7, -1)));
    frag = vec4(vec3(light_value), 1.);
}