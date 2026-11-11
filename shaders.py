# -*- coding: utf-8 -*-
"""GLSL shader kaynaklari (aydinlatma ve post-process)."""

VS_LIT = """#version 330
in vec3 vertexPosition; in vec2 vertexTexCoord; in vec3 vertexNormal; in vec4 vertexColor;
uniform mat4 mvp; uniform mat4 matModel; uniform mat4 matNormal;
out vec3 fragPosition; out vec3 fragNormal; out vec4 fragColor;
void main(){
  fragPosition = vec3(matModel*vec4(vertexPosition,1.0));
  fragNormal = normalize(vec3(matNormal*vec4(vertexNormal,1.0)));
  fragColor = vertexColor;
  gl_Position = mvp*vec4(vertexPosition,1.0);
}"""

FS_LIT = """#version 330
in vec3 fragPosition; in vec3 fragNormal; in vec4 fragColor;
uniform vec4 colDiffuse; uniform vec3 viewPos; uniform float pattern;
out vec4 finalColor;
float hash(vec2 p){ return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453); }
float noise(vec2 p){ vec2 i=floor(p), f=fract(p); f=f*f*(3.0-2.0*f);
  return mix(mix(hash(i),hash(i+vec2(1,0)),f.x),mix(hash(i+vec2(0,1)),hash(i+vec2(1,1)),f.x),f.y); }
void main(){
  vec3 N = normalize(fragNormal);
  vec3 base = colDiffuse.rgb;
  float ao = 1.0;
  if(pattern>0.5){
    vec2 uv = (abs(N.y)>0.5) ? fragPosition.xz : ((abs(N.x)>abs(N.z)) ? fragPosition.zy : fragPosition.xy);
    float n = noise(uv*5.0)*0.5 + noise(uv*23.0)*0.3 + noise(uv*90.0)*0.2;
    base *= 0.72 + 0.5*n;
    vec2 gq = abs(fract(uv/2.0+0.5)-0.5);
    float line = smoothstep(0.0,0.018,min(gq.x,gq.y));
    base *= mix(0.62,1.0,line);
    ao = mix(0.55,1.0,clamp(fragPosition.y/2.2,0.0,1.0));
  }
  vec3 L = normalize(vec3(0.45,0.85,0.30));
  vec3 V = normalize(viewPos - fragPosition);
  float diff = max(dot(N,L),0.0);
  vec3 amb = mix(vec3(0.20,0.19,0.18), vec3(0.34,0.40,0.52), N.y*0.5+0.5);
  float rim = pow(1.0-max(dot(N,V),0.0),3.0)*0.18;
  vec3 H = normalize(L+V);
  float spec = pow(max(dot(N,H),0.0),48.0)*(pattern>0.5?0.10:0.45);
  vec3 col = base*(amb*ao + diff*vec3(1.05,0.95,0.82)*1.05*mix(0.7,1.0,ao)) + spec + rim*vec3(0.4,0.55,0.7);
  float dist = length(viewPos-fragPosition);
  float f = 1.0-exp(-dist*0.010);
  col = mix(col, vec3(0.62,0.69,0.77), clamp(f,0.0,0.85));
  finalColor = vec4(col, colDiffuse.a);
}"""

VS_POST = """#version 330
in vec3 vertexPosition; in vec2 vertexTexCoord; in vec4 vertexColor;
uniform mat4 mvp;
out vec2 fragTexCoord; out vec4 fragColor;
void main(){ fragTexCoord=vertexTexCoord; fragColor=vertexColor; gl_Position=mvp*vec4(vertexPosition,1.0); }"""

FS_POST = """#version 330
in vec2 fragTexCoord; in vec4 fragColor;
uniform sampler2D texture0; uniform vec4 colDiffuse;
uniform vec2 res; uniform float time; uniform float wave; uniform float hurt;
uniform float digital; uniform float ult; uniform float fx;
out vec4 finalColor;
float hash(vec2 p){ return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453); }
vec3 aces(vec3 x){ return clamp((x*(2.51*x+0.03))/(x*(2.43*x+0.59)+0.14),0.0,1.0); }
void main(){
  vec2 uv = fragTexCoord;
  float asp = res.x/res.y;
  if(digital>0.01){
    float row=floor(uv.y*48.0);
    float gl=step(0.92,hash(vec2(row,floor(time*12.0))));
    uv.x += gl*(hash(vec2(row,time))-0.5)*0.07*digital;
  }
  float m=0.0, glyph=0.0, edge=0.0;
  if(wave>=0.0){
    vec2 p=(uv-vec2(0.5))*vec2(asp,1.0);
    float r=length(p);
    float front=wave*1.7;
    float d=front-r;
    m=smoothstep(0.0,0.02,d)*(1.0-smoothstep(0.0,0.36,d));
    edge=exp(-abs(d)*60.0);
    uv += normalize(p+vec2(1e-5))*sin(d*55.0)*0.006*(m+edge)*vec2(1.0/asp,1.0);
    float cs=0.052; vec2 q=p/cs; vec2 cell=floor(q); vec2 lp=fract(q)*2.0-1.0;
    float one=step(0.5,hash(cell+floor(time*9.0)));
    float z=abs(length(lp*vec2(1.25,0.85))-0.78);
    float g0=1.0-smoothstep(0.10,0.20,z);
    float bar=(1.0-smoothstep(0.12,0.20,abs(lp.x)))*(1.0-smoothstep(0.76,0.86,abs(lp.y)));
    float flg=(1.0-smoothstep(0.10,0.18,abs(lp.y-0.75-lp.x)))*step(lp.x,0.0)*step(-0.6,lp.x);
    glyph=mix(g0,max(bar,flg),one)*(0.45+0.55*hash(cell*1.7))*m;
  }
  vec2 off=(uv-0.5)*(0.002+hurt*0.012+m*0.01)*(fx>0.5?1.0:0.0);
  vec3 col;
  col.r=texture(texture0,uv+off).r; col.g=texture(texture0,uv).g; col.b=texture(texture0,uv-off).b;
  if(fx>0.5){
    vec3 bl=vec3(0.0);
    for(int i=0;i<8;i++){
      float a=float(i)*0.7854;
      vec2 o=vec2(cos(a),sin(a));
      bl+=max(texture(texture0,uv+o*3.0/res).rgb-0.72,0.0);
      bl+=max(texture(texture0,uv+o*9.0/res).rgb-0.72,0.0)*0.7;
    }
    col+=bl*0.10;
    col=mix(col,aces(col*1.22),0.75);
    float lum=dot(col,vec3(0.299,0.587,0.114));
    col=mix(vec3(lum),col,1.12);
    float v=smoothstep(1.0,0.3,length((uv-0.5)*vec2(asp*0.75,1.0)));
    col*=mix(1.0,v,0.6);
    col+=(hash(uv*res+time)-0.5)*0.05;
  }
  col += vec3(0.10,1.0,0.78)*(glyph*1.7+edge*m*0.9);
  if(digital>0.01){
    float lum=dot(col,vec3(0.299,0.587,0.114));
    col=mix(col,vec3(lum)*vec3(0.35,1.0,0.8)*1.2,digital*0.75);
    col*=1.0-digital*0.18*sin(uv.y*res.y*1.6);
  }
  if(ult>0.01){
    col=mix(col,col*vec3(1.12,0.78,0.95),ult*0.4);
    col+=vec3(0.5,0.0,0.25)*ult*pow(length(uv-0.5)*1.5,3.0)*(0.6+0.4*sin(time*6.0));
  }
  col+=vec3(0.65,0.0,0.0)*hurt*pow(length(uv-0.5)*1.5,2.0);
  finalColor=vec4(col,1.0);
}"""
