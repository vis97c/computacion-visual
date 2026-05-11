import React, { useRef, useState, useEffect } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { Html, Environment, ContactShadows, OrbitControls, Float } from '@react-three/drei';
import { useControls } from 'leva';
import * as THREE from 'three';

function InteractiveObject({ active, setActive, objectRef }) {
  // Leva controls for sliders and UI settings
  const { color, scale, speed, floatIntensity } = useControls('Ajustes del Objeto', {
    color: { value: '#aa3bff', label: 'Color' },
    scale: { value: 1.5, min: 0.5, max: 3, step: 0.1, label: 'Escala' },
    speed: { value: 1, min: 0, max: 5, step: 0.1, label: 'Velocidad' },
    floatIntensity: { value: 2, min: 0, max: 10, step: 0.1, label: 'Flotación' }
  });

  // Animation using useFrame
  useFrame((state, delta) => {
    if (active && objectRef.current) {
      objectRef.current.rotation.x += delta * speed;
      objectRef.current.rotation.y += delta * speed * 0.8;
    }
  });

  return (
    <Float speed={speed * 2} rotationIntensity={active ? 1 : 0} floatIntensity={floatIntensity}>
      <mesh
        ref={objectRef}
        scale={scale}
        onClick={(e) => {
          e.stopPropagation();
          setActive(!active); // Clicks on object with onClick
        }}
        onPointerOver={() => document.body.style.cursor = 'pointer'}
        onPointerOut={() => document.body.style.cursor = 'auto'}
      >
        <boxGeometry args={[1, 1, 1]} />
        <meshPhysicalMaterial 
          color={active ? color : '#555555'} 
          roughness={0.1}
          metalness={0.8}
          clearcoat={1}
          clearcoatRoughness={0.1}
        />
        
        {/* Html UI superimposed using @react-three/drei */}
        <Html position={[0, 1.2, 0]} center distanceFactor={10}>
          <div style={{
            background: 'rgba(25, 25, 25, 0.8)',
            padding: '10px 20px',
            borderRadius: '12px',
            backdropFilter: 'blur(10px)',
            color: 'white',
            fontWeight: 'bold',
            border: `1px solid ${active ? color : '#555'}`,
            transition: 'all 0.3s ease',
            pointerEvents: 'none',
            userSelect: 'none',
            whiteSpace: 'nowrap',
            boxShadow: `0 0 20px ${active ? color + '40' : 'transparent'}`
          }}>
            Estado: {active ? 'ROTANDO' : 'PAUSADO'}
          </div>
        </Html>
      </mesh>
    </Float>
  );
}

function SceneControls({ orbitRef, objectRef }) {
  const { camera } = useThree();

  // Teclas con useEffect y window.addEventListener("keydown", ...)
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key.toLowerCase() === 'r') {
        // Reset camera position
        camera.position.set(0, 0, 5);
        camera.lookAt(0, 0, 0);
        
        // Reset OrbitControls center
        if (orbitRef.current) {
          orbitRef.current.target.set(0, 0, 0);
          orbitRef.current.update();
        }

        // Reset Object position and rotation
        if (objectRef.current) {
          objectRef.current.position.set(0, 0, 0);
          objectRef.current.rotation.set(0, 0, 0);
        }
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [camera, orbitRef, objectRef]);

  // useThree().events example for pointer tracking
  useFrame(({ pointer }) => {
    // You can access pointer.x and pointer.y here if needed
  });

  return null;
}

export default function App() {
  const [active, setActive] = useState(true);
  const orbitRef = useRef();
  const objectRef = useRef();

  return (
    <>
      {/* Canvas for ThreeJS content */}
      <Canvas camera={{ position: [0, 0, 5], fov: 50 }} shadows>
        <color attach="background" args={['#101014']} />
        <ambientLight intensity={0.5} />
        <spotLight position={[10, 10, 10]} angle={0.15} penumbra={1} intensity={1} castShadow />
        
        <InteractiveObject active={active} setActive={setActive} objectRef={objectRef} />

        {/* OrbitControls provides a much more stable rotation drag */}
        <OrbitControls ref={orbitRef} makeDefault enableDamping dampingFactor={0.05} />

        <SceneControls orbitRef={orbitRef} objectRef={objectRef} />
        
        <Environment preset="city" />
        <ContactShadows position={[0, -1.5, 0]} opacity={0.4} scale={20} blur={1.5} far={4.5} />
      </Canvas>

      {/* Global HTML UI Overlay using react-dom (React elements over Canvas) */}
      <div style={{
        position: 'absolute',
        top: 20,
        left: 20,
        color: 'white',
        pointerEvents: 'none',
        fontFamily: 'system-ui, sans-serif'
      }}>
        <h1 style={{ 
          margin: 0, 
          fontSize: '28px', 
          fontWeight: '800', 
          background: 'linear-gradient(90deg, #c084fc, #aa3bff)', 
          WebkitBackgroundClip: 'text', 
          WebkitTextFillColor: 'transparent' 
        }}>
          Three.js + Interfaz React
        </h1>
        <p style={{ margin: '8px 0 0 0', opacity: 0.8, fontSize: '15px', lineHeight: '1.5' }}>
          🖱️ Haz clic en el objeto 3D para rotar/pausar.<br/>
          ⌨️ Presiona <b>'R'</b> para reiniciar la cámara y el objeto.<br/>
          ✋ Arrastra para rotar la cámara alrededor del objeto.
        </p>
      </div>

      <div style={{
        position: 'absolute',
        bottom: 30,
        left: '50%',
        transform: 'translateX(-50%)',
        pointerEvents: 'auto'
      }}>
         {/* Button using react-dom */}
         <button 
           onClick={() => setActive(!active)}
           style={{
             background: active ? '#aa3bff' : '#333',
             color: 'white',
             border: 'none',
             padding: '14px 28px',
             borderRadius: '12px',
             cursor: 'pointer',
             fontSize: '16px',
             fontWeight: 'bold',
             transition: 'all 0.3s ease',
             boxShadow: active ? '0 4px 20px rgba(170, 59, 255, 0.5)' : 'none',
             display: 'flex',
             alignItems: 'center',
             gap: '8px'
           }}
           onMouseOver={(e) => e.currentTarget.style.transform = 'scale(1.05)'}
           onMouseOut={(e) => e.currentTarget.style.transform = 'scale(1)'}
         >
           {active ? '⏸ Pausar Animación' : '▶ Iniciar Animación'}
         </button>
      </div>
    </>
  );
}
