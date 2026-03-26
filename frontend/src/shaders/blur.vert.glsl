attribute vec2 a_position;
attribute float a_size;
attribute float a_angle;
attribute vec4 a_color;

uniform mat3 u_matrix;
uniform float u_sizeRatio;
uniform float u_pixelRatio;

varying vec4 v_color;
varying float v_border;

void main() {
  gl_Position = vec4((u_matrix * vec3(a_position, 1)).xy, 0, 1);

  float size = a_size * u_sizeRatio * u_pixelRatio;
  v_border = (0.5 / size);
  v_color = a_color;
  
  gl_PointSize = size * 2.5; 
}
