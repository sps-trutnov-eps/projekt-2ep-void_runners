#version 330

// define seg //

uniform sampler2D hdr_base;

uniform int bloom_enabled;
uniform float bloom_strength;
uniform sampler2D hdr_bloom;

uniform float exposure;

in vec2 frag_uv;
out vec4 frag;

// fetch final color value from hdr buffers
vec3 mix_final() {
    vec3 base_frag = texture(hdr_base, frag_uv).rgb;
    
    if (bloom_enabled != 0) {
        vec3 bloom_frag = texture(hdr_bloom, frag_uv).rgb;
        return mix(base_frag, bloom_frag, bloom_strength);
    }

    return base_frag;
}

void main() {
    vec3 hdr_frag = mix_final();

    // perform tonemapping and gamma correct
    vec3 sdr_frag = vec3(1.0) - exp(-hdr_frag * exposure);

    const float gamma = 2.2;
    sdr_frag = pow(sdr_frag, vec3(1.0 / gamma));

    frag = vec4(sdr_frag, 1.0);
}