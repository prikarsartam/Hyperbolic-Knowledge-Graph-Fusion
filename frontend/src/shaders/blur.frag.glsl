precision mediump float;

varying vec4 v_color;
varying float v_border;

uniform float u_smoothing;

void main() {
    float dist = length(gl_PointCoord - vec2(0.5));
    if (dist > 0.5) discard;

    float t = smoothstep(0.5 - u_smoothing, 0.5, dist);
    
    // Hyperbolic halo effect blending
    vec4 final_color = mix(v_color, vec4(v_color.rgb, 0.0), t);
    gl_FragColor = final_color;
}
