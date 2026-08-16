import React, { useRef, useMemo } from 'react';
import { useFrame, useThree } from '@react-three/fiber';
import * as THREE from 'three';

export function ParticleSwarmScene({ activeSection, isAnalyzing, result, model, isMobile }) {
  const count = isMobile ? 150 : 500;
  const meshRef = useRef();
  const { viewport } = useThree();
  
  // Store the target state interpolator
  const stateLerp = useRef(0);
  
  // Create particle base data
  const particles = useMemo(() => {
    const temp = [];
    for (let i = 0; i < count; i++) {
      const theta = Math.random() * 2 * Math.PI;
      const phi = Math.acos(2 * Math.random() - 1);
      const r = 10 + Math.random() * 20; // Wide initial spread
      
      const x = r * Math.sin(phi) * Math.cos(theta);
      const y = r * Math.sin(phi) * Math.sin(theta);
      const z = r * Math.cos(phi);
      
      temp.push({
        originX: x, originY: y, originZ: z,
        x, y, z,
        speed: 0.05 + Math.random() * 0.15,
        offset: Math.random() * Math.PI * 2,
        gridX: (i % 10) - 5,
        gridY: Math.floor((i % 100) / 10) - 5,
        gridZ: Math.floor(i / 100) - 2,
      });
    }
    return temp;
  }, [count]);

  const dummy = useMemo(() => new THREE.Object3D(), []);
  const currentColor = useRef(new THREE.Color('#333333'));

  useFrame((state) => {
    if (!meshRef.current) return;
    const time = state.clock.getElapsedTime();
    
    // Determine Target Color based on section and result
    let targetColor = new THREE.Color('#333333'); // Default dim grey
    
    if (activeSection === 2) {
      targetColor = new THREE.Color('#2563eb'); // PSO Accent
    } else if (activeSection === 4 && result && !isAnalyzing) {
      // Results section
      if (model === 'compare') {
        targetColor = result.disagreement ? new THREE.Color('#ffaa00') : new THREE.Color('#2563eb');
      } else {
        targetColor = result.prediction === 'REAL' ? new THREE.Color('#00ff66') : new THREE.Color('#ff3333');
      }
    } else if (isAnalyzing) {
      targetColor = new THREE.Color('#ffffff'); // Analyzing white flash
    }
    
    currentColor.current.lerp(targetColor, 0.05);
    meshRef.current.material.color.copy(currentColor.current);

    particles.forEach((p, i) => {
      let targetX = p.originX;
      let targetY = p.originY;
      let targetZ = p.originZ;
      let scale = 0.03;

      // Section 0: HERO (Distant, slow, vast)
      if (activeSection === 0) {
        targetX = p.originX + Math.sin(time * p.speed + p.offset) * 2;
        targetY = p.originY + Math.cos(time * p.speed + p.offset) * 2;
        targetZ = p.originZ + Math.sin(time * p.speed * 0.5 + p.offset) * 2;
      }
      
      // Section 1: PIPELINE (Grid / Neural layers)
      else if (activeSection === 1) {
        targetX = p.gridX * 1.5;
        targetY = p.gridY * 1.5;
        targetZ = p.gridZ * 4 + Math.sin(time + p.gridX) * 0.5;
        scale = 0.05;
      }
      
      // Section 2: PSO (Swarming to a specific point)
      else if (activeSection === 2) {
        // Converge tightly
        const r = 3 + Math.sin(time * 2 + p.offset);
        const theta = time * p.speed * 5 + p.offset;
        targetX = r * Math.cos(theta);
        targetY = r * Math.sin(theta);
        targetZ = (p.gridZ * 0.5) + Math.cos(time + p.offset) * 2;
        scale = 0.06;
      }

      // Section 3: DETECTOR (Anticipating)
      else if (activeSection === 3) {
        if (isAnalyzing) {
          // Spiraling inwards
          const r = Math.max(0.5, 10 - (time % 2) * 10);
          targetX = r * Math.cos(time * 10 + p.offset);
          targetY = r * Math.sin(time * 10 + p.offset);
          targetZ = p.originZ * 0.1;
          scale = 0.1;
        } else {
          // Ring formation
          targetX = 10 * Math.cos(p.offset + time * 0.1);
          targetY = 10 * Math.sin(p.offset + time * 0.1);
          targetZ = Math.sin(p.offset * 3 + time) * 2;
        }
      }

      // Section 4: RESULT
      else if (activeSection === 4) {
        // Explosion/Pulse based on result
        const pulse = 1 + Math.sin(time * 3 + p.offset) * 0.2;
        targetX = p.originX * 0.3 * pulse;
        targetY = p.originY * 0.3 * pulse;
        targetZ = p.originZ * 0.3 * pulse;
        scale = 0.08;
      }
      
      // Section 5: RESEARCH (Fade away)
      else {
        targetY = p.originY - 20; // Fall down
      }

      // Lerp particle to target
      p.x = THREE.MathUtils.lerp(p.x, targetX, 0.05);
      p.y = THREE.MathUtils.lerp(p.y, targetY, 0.05);
      p.z = THREE.MathUtils.lerp(p.z, targetZ, 0.05);

      dummy.position.set(p.x, p.y, p.z);
      dummy.scale.set(scale, scale, scale);
      dummy.updateMatrix();
      meshRef.current.setMatrixAt(i, dummy.matrix);
    });
    
    meshRef.current.instanceMatrix.needsUpdate = true;
    
    // Global rotation based on scroll or time
    meshRef.current.rotation.y = time * 0.02;
    meshRef.current.rotation.x = time * 0.01;
  });

  return (
    <instancedMesh ref={meshRef} args={[null, null, count]}>
      <sphereGeometry args={[1, 8, 8]} />
      <meshBasicMaterial />
    </instancedMesh>
  );
}
