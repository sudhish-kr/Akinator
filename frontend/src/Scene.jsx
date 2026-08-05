import { useMemo, useRef } from "react";
import { Canvas, useFrame } from "@react-three/fiber";
import { MeshDistortMaterial, Sparkles, Stars } from "@react-three/drei";
import { Bloom, EffectComposer, Vignette } from "@react-three/postprocessing";
import * as THREE from "three";

// Orb color shifts with confidence: cyan (searching) -> violet (closing in) -> gold (certain)
function orbTargetColor(confidence, mood) {
  if (mood === "celebrate") return "#ffd24d";
  if (confidence > 0.72) return "#ffb84d";
  if (confidence > 0.45) return "#b44dff";
  return "#3fd6ff";
}

function MindOrb({ confidence, mood }) {
  const mesh = useRef();
  const material = useRef();
  const target = useMemo(() => new THREE.Color(), []);

  useFrame((state, delta) => {
    const t = state.clock.elapsedTime;
    const thinking = mood === "thinking";
    const celebrate = mood === "celebrate";

    const pulseSpeed = celebrate ? 9 : thinking ? 6 : 1.6;
    const pulseAmp = celebrate ? 0.14 : thinking ? 0.09 : 0.05;
    mesh.current.scale.setScalar(1 + Math.sin(t * pulseSpeed) * pulseAmp);

    mesh.current.rotation.y += delta * (celebrate ? 2.4 : thinking ? 1.3 : 0.18);
    mesh.current.rotation.z += delta * 0.05;

    target.set(orbTargetColor(confidence, mood));
    material.current.color.lerp(target, delta * 2.2);
    material.current.emissive.lerp(target, delta * 2.2);
    material.current.emissiveIntensity = THREE.MathUtils.lerp(
      material.current.emissiveIntensity,
      celebrate ? 2.2 : 0.85 + confidence * 0.9,
      delta * 3
    );
    material.current.distort = THREE.MathUtils.lerp(
      material.current.distort,
      celebrate ? 0.62 : thinking ? 0.55 : 0.34,
      delta * 3
    );
  });

  return (
    <mesh ref={mesh}>
      <icosahedronGeometry args={[1.15, 48]} />
      <MeshDistortMaterial
        ref={material}
        color="#3fd6ff"
        emissive="#3fd6ff"
        emissiveIntensity={0.85}
        roughness={0.12}
        metalness={0.25}
        distort={0.34}
        speed={2.6}
      />
    </mesh>
  );
}

function OrbitRing({ radius, tilt, speed, color, opacity }) {
  const ring = useRef();
  useFrame((_, delta) => {
    ring.current.rotation.z += delta * speed;
  });
  return (
    <group rotation={[tilt, 0.4, 0]}>
      <mesh ref={ring}>
        <torusGeometry args={[radius, 0.012, 16, 128]} />
        <meshBasicMaterial color={color} transparent opacity={opacity} blending={THREE.AdditiveBlending} />
      </mesh>
    </group>
  );
}

function SwirlingParticles({ mood }) {
  const points = useRef();
  const positions = useMemo(() => {
    const count = 900;
    const arr = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      const angle = Math.random() * Math.PI * 2;
      const radius = 2.2 + Math.random() * 3.5;
      const y = (Math.random() - 0.5) * 2.4;
      arr[i * 3] = Math.cos(angle) * radius;
      arr[i * 3 + 1] = y;
      arr[i * 3 + 2] = Math.sin(angle) * radius;
    }
    return arr;
  }, []);

  useFrame((_, delta) => {
    points.current.rotation.y += delta * (mood === "thinking" ? 0.55 : 0.08);
  });

  return (
    <points ref={points}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" count={positions.length / 3} array={positions} itemSize={3} />
      </bufferGeometry>
      <pointsMaterial
        size={0.025}
        color="#7fd4ff"
        transparent
        opacity={0.75}
        sizeAttenuation
        blending={THREE.AdditiveBlending}
        depthWrite={false}
      />
    </points>
  );
}

function CameraDrift() {
  useFrame((state) => {
    const t = state.clock.elapsedTime;
    state.camera.position.x = Math.sin(t * 0.12) * 0.35;
    state.camera.position.y = Math.cos(t * 0.1) * 0.25;
    state.camera.lookAt(0, 0, 0);
  });
  return null;
}

export default function Scene({ confidence, mood }) {
  return (
    <Canvas
      className="scene-canvas"
      camera={{ position: [0, 0, 6.4], fov: 55 }}
      gl={{ antialias: true, alpha: false }}
    >
      <color attach="background" args={["#03020a"]} />
      <fog attach="fog" args={["#03020a", 7, 16]} />

      <ambientLight intensity={0.25} />
      <pointLight position={[6, 4, 6]} intensity={40} color="#6f7cff" />
      <pointLight position={[-6, -3, -4]} intensity={25} color="#ff4de1" />

      <Stars radius={60} depth={40} count={3200} factor={3.2} saturation={0.4} fade speed={0.6} />
      <SwirlingParticles mood={mood} />
      <Sparkles
        count={mood === "celebrate" ? 220 : 90}
        scale={[7, 5, 7]}
        size={mood === "celebrate" ? 9 : 4.5}
        speed={mood === "celebrate" ? 1.6 : 0.45}
        color={mood === "celebrate" ? "#ffd24d" : "#9be8ff"}
      />

      <MindOrb confidence={confidence} mood={mood} />
      <OrbitRing radius={2.05} tilt={1.15} speed={0.5} color="#4dd8ff" opacity={0.5} />
      <OrbitRing radius={2.45} tilt={-0.9} speed={-0.32} color="#b44dff" opacity={0.4} />
      <OrbitRing radius={2.9} tilt={0.35} speed={0.18} color="#ff4de1" opacity={0.25} />

      <CameraDrift />

      <EffectComposer>
        <Bloom intensity={1.15} luminanceThreshold={0.18} luminanceSmoothing={0.85} mipmapBlur />
        <Vignette eskil={false} offset={0.18} darkness={0.85} />
      </EffectComposer>
    </Canvas>
  );
}
