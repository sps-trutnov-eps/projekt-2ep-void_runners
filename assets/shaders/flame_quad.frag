#version 330

out vec4 frag;
flat in float frag_lifetime;
flat in int sprite_index;

uniform sampler2D albedo;
const int sheet_sprite_num = 25;

void main() {
    vec2 uv_orig = gl_PointCoord;
    uv_orig.x /= sheet_sprite_num;

    vec2 uv1 = uv_orig + vec2(floor(frag_lifetime) / sheet_sprite_num, 0.);
    vec2 uv2 = uv_orig + vec2(ceil(frag_lifetime) / sheet_sprite_num, 0.);

    // frag = vec4(frag_lifetime, frag_lifetime, frag_lifetime, 1.);
    frag = mix(texture(albedo, uv1), texture(albedo, uv2), mod(frag_lifetime, 1.)) * vec4(vec3(frag_lifetime * 2), 1.);
}