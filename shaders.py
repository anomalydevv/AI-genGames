
# -*- coding: utf-8 -*-
"""GLSL shader kaynaklari (aydınlatma ve post-process)."""

VS_LIT = """#version 330

in vec3 vertexPosition;
in vec2 vertexTexCoord;
in vec3 vertexNormal;
in vec4 vertexColor;

uniform mat4 mvp;
uniform mat4 matModel;
uniform mat4 matNormal;

out vec3 fragPosition;
out vec3 fragNormal;
out vec4 fragColor;

void main()
{
    vec4 worldPosition = matModel * vec4(vertexPosition, 1.0);

    fragPosition = worldPosition.xyz;
    fragNormal = normalize(mat3(matNormal) * vertexNormal);
    fragColor = vertexColor;

    gl_Position = mvp * vec4(vertexPosition, 1.0);
}
"""

FS_LIT = """#version 330

in vec3 fragPosition;
in vec3 fragNormal;
in vec4 fragColor;

uniform vec4 colDiffuse;
uniform vec3 viewPos;
uniform float pattern;
uniform float vm;

out vec4 finalColor;

const float PI = 3.14159265;

float hash(vec2 p)
{
    return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

float noise(vec2 p)
{
    vec2 i = floor(p);
    vec2 f = fract(p);

    f = f * f * (3.0 - 2.0 * f);

    float a = hash(i);
    float b = hash(i + vec2(1.0, 0.0));
    float c = hash(i + vec2(0.0, 1.0));
    float d = hash(i + vec2(1.0, 1.0));

    return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);
}

float fbm(vec2 p)
{
    float value = 0.0;
    float amplitude = 0.5;

    for (int i = 0; i < 5; i++)
    {
        value += noise(p) * amplitude;
        p *= 2.03;
        amplitude *= 0.5;
    }

    return value;
}

float fresnel(vec3 N, vec3 V)
{
    return pow(1.0 - max(dot(N, V), 0.0), 5.0);
}

void main()
{
    vec3 N = normalize(fragNormal);
    vec3 V = normalize(viewPos - fragPosition);

    vec3 base = colDiffuse.rgb * fragColor.rgb;

    float ao = 1.0;
    float roughness = 0.72;

    // Procedural material.
    if (pattern > 0.5)
    {
        vec2 uv;

        if (abs(N.y) > 0.5)
            uv = fragPosition.xz;
        else if (abs(N.x) > abs(N.z))
            uv = fragPosition.zy;
        else
            uv = fragPosition.xy;

        float largeNoise = fbm(uv * 2.0);
        float mediumNoise = fbm(uv * 9.0);
        float fineNoise = noise(uv * 65.0);

        float detail =
            largeNoise * 0.50 +
            mediumNoise * 0.32 +
            fineNoise * 0.18;

        base *= 0.72 + detail * 0.55;

        // Surface imperfections.
        float pores = noise(uv * 110.0);
        base *= 0.94 + pores * 0.10;

        // Surface grid.
        vec2 grid = abs(fract(uv / 2.0 + 0.5) - 0.5);

        float gridLine = 1.0 - smoothstep(
            0.0,
            0.018,
            min(grid.x, grid.y)
        );

        base *= 1.0 - gridLine * 0.20;

        // Height-based approximation of ambient occlusion.
        float heightAO = smoothstep(
            -0.5,
            2.5,
            fragPosition.y
        );

        ao *= mix(0.58, 1.0, heightAO);

        roughness = 0.88;
    }

    // Directional lighting.
    vec3 L = normalize(
        mix(
            vec3(0.45, 0.85, 0.30),
            vec3(0.32, 0.58, -0.75),
            vm
        )
    );

    float NdotL = max(dot(N, L), 0.0);
    float NdotV = max(dot(N, V), 0.0);

    vec3 H = normalize(L + V);

    // Ambient sky lighting.
    float skyFactor = N.y * 0.5 + 0.5;

    vec3 skyColor = vec3(0.38, 0.46, 0.62);
    vec3 groundColor = vec3(0.18, 0.16, 0.14);

    vec3 ambient = mix(
        groundColor,
        skyColor,
        skyFactor
    );

    ambient *= mix(1.0, 1.2, vm);

    // Diffuse.
    vec3 lightColor = vec3(1.0, 0.94, 0.82);

    float diffuse = NdotL;

    diffuse *= mix(1.05, 0.68, vm);

    // Blinn-Phong specular.
    float shininess = mix(64.0, 12.0, roughness);

    float specular = pow(
        max(dot(N, H), 0.0),
        shininess
    );

    specular *= mix(0.42, 0.12, roughness);
    specular *= mix(1.0, 0.55, vm);

    // Fresnel.
    float F = fresnel(N, V);

    float rim = F * mix(0.16, 0.28, vm);

    vec3 rimColor = vec3(0.42, 0.58, 0.78);

    // Final lighting.
    vec3 color =
        base * ambient * ao +
        base * lightColor * diffuse * ao +
        lightColor * specular +
        rimColor * rim;

    // Distance fog.
    float distanceToCamera = length(viewPos - fragPosition);

    float fog = 1.0 - exp(
        -distanceToCamera * 0.010
    );

    vec3 fogColor = mix(
        vec3(0.62, 0.69, 0.77),
        vec3(0.20, 0.25, 0.34),
        vm
    );

    fog = clamp(fog, 0.0, 0.85);
    fog *= mix(1.0, 0.15, vm);

    color = mix(color, fogColor, fog);

    finalColor = vec4(color, colDiffuse.a * fragColor.a);
}
"""

VS_POST = """#version 330

in vec3 vertexPosition;
in vec2 vertexTexCoord;
in vec4 vertexColor;

uniform mat4 mvp;

out vec2 fragTexCoord;
out vec4 fragColor;

void main()
{
    fragTexCoord = vertexTexCoord;
    fragColor = vertexColor;

    gl_Position = mvp * vec4(vertexPosition, 1.0);
}
"""

FS_POST = """#version 330

in vec2 fragTexCoord;
in vec4 fragColor;

uniform sampler2D texture0;
uniform vec4 colDiffuse;

uniform vec2 res;
uniform float time;
uniform float wave;
uniform float hurt;
uniform float digital;
uniform float ult;
uniform float fx;

out vec4 finalColor;

float hash(vec2 p)
{
    return fract(
        sin(dot(p, vec2(127.1, 311.7))) * 43758.5453
    );
}

vec3 aces(vec3 x)
{
    return clamp(
        (x * (2.51 * x + 0.03)) /
        (x * (2.43 * x + 0.59) + 0.14),
        0.0,
        1.0
    );
}

void main()
{
    vec2 uv = fragTexCoord;

    float asp = res.x / max(res.y, 1.0);

    // Digital glitch.
    if (digital > 0.01)
    {
        float row = floor(uv.y * 48.0);

        float glitch = step(
            0.92,
            hash(vec2(row, floor(time * 12.0)))
        );

        uv.x += glitch *
            (hash(vec2(row, time)) - 0.5) *
            0.07 * digital;
    }

    float m = 0.0;
    float glyph = 0.0;
    float edge = 0.0;

    // Wave distortion.
    if (wave >= 0.0)
    {
        vec2 p = (uv - 0.5) * vec2(asp, 1.0);

        float r = length(p);
        float front = wave * 1.7;
        float d = front - r;

        m = smoothstep(0.0, 0.02, d) *
            (1.0 - smoothstep(0.0, 0.36, d));

        edge = exp(-abs(d) * 60.0);

        vec2 direction = normalize(p + vec2(0.00001));

        uv += direction *
            sin(d * 55.0) *
            0.006 *
            (m + edge) *
            vec2(1.0 / asp, 1.0);

        float cs = 0.052;

        vec2 q = p / cs;
        vec2 cell = floor(q);
        vec2 lp = fract(q) * 2.0 - 1.0;

        float one = step(
            0.5,
            hash(cell + floor(time * 9.0))
        );

        float z = abs(
            length(lp * vec2(1.25, 0.85)) - 0.78
        );

        float g0 = 1.0 - smoothstep(0.10, 0.20, z);

        float bar =
            (1.0 - smoothstep(0.12, 0.20, abs(lp.x))) *
            (1.0 - smoothstep(0.76, 0.86, abs(lp.y)));

        float flg =
            (1.0 - smoothstep(
                0.10,
                0.18,
                abs(lp.y - 0.75 - lp.x)
            )) *
            step(lp.x, 0.0) *
            step(-0.6, lp.x);

        glyph = mix(
            g0,
            max(bar, flg),
            one
        ) * (0.45 + 0.55 * hash(cell * 1.7)) * m;
    }

    // Chromatic aberration.
    vec2 off = (uv - 0.5) *
        (0.002 + hurt * 0.012 + m * 0.01) *
        (fx > 0.5 ? 1.0 : 0.0);

    vec3 col;

    col.r = texture(texture0, uv + off).r;
    col.g = texture(texture0, uv).g;
    col.b = texture(texture0, uv - off).b;

    if (fx > 0.5)
    {
        // Bloom.
        vec3 bloom = vec3(0.0);

        for (int i = 0; i < 8; i++)
        {
            float angle = float(i) * 0.785398;

            vec2 direction = vec2(
                cos(angle),
                sin(angle)
            );

            vec3 sample1 = texture(
                texture0,
                uv + direction * 3.0 / res
            ).rgb;

            vec3 sample2 = texture(
                texture0,
                uv + direction * 9.0 / res
            ).rgb;

            bloom += max(sample1 - 0.72, 0.0);
            bloom += max(sample2 - 0.72, 0.0) * 0.7;
        }

        col += bloom * 0.10;

        // HDR tone mapping.
        col = mix(
            col,
            aces(col * 1.22),
            0.75
        );

        // Saturation.
        float lum = dot(
            col,
            vec3(0.299, 0.587, 0.114)
        );

        col = mix(
            vec3(lum),
            col,
            1.12
        );

        // Cinematic vignette.
        float vignetteDistance = length(
            (uv - 0.5) * vec2(asp * 0.75, 1.0)
        );

        float vignette = smoothstep(
            1.0,
            0.3,
            vignetteDistance
        );

        col *= mix(1.0, vignette, 0.6);

        // Film grain.
        float grain = hash(
            uv * res + time
        ) - 0.5;

        col += grain * 0.035;
    }

    // Wave energy.
    col += vec3(0.10, 1.0, 0.78) *
        (glyph * 1.7 + edge * m * 0.9);

    // Digital mode.
    if (digital > 0.01)
    {
        float lum = dot(
            col,
            vec3(0.299, 0.587, 0.114)
        );

        col = mix(
            col,
            vec3(lum) * vec3(0.35, 1.0, 0.8) * 1.2,
            digital * 0.75
        );

        float scanline = sin(
            uv.y * res.y * 1.6
        );

        col *= 1.0 - digital * 0.18 * scanline;
    }

    // Ultimate effect.
    if (ult > 0.01)
    {
        col = mix(
            col,
            col * vec3(1.12, 0.78, 0.95),
            ult * 0.4
        );

        float energy = 0.6 + 0.4 * sin(time * 6.0);

        col += vec3(0.5, 0.0, 0.25) *
            ult *
            pow(length(uv - 0.5) * 1.5, 3.0) *
            energy;
    }

    // Damage effect.
    col += vec3(0.65, 0.0, 0.0) *
        hurt *
        pow(length(uv - 0.5) * 1.5, 2.0);

    finalColor = vec4(col, 1.0);
}
"""
