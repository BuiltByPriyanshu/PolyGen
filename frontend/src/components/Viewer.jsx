import { Suspense, useEffect, useState } from "react";
import { Canvas } from "@react-three/fiber";
import { Bounds, Center, Html, OrbitControls, useGLTF, useProgress } from "@react-three/drei";
import ViewerErrorBoundary from "./ViewerErrorBoundary.jsx";

function countGeometry(scene) {
  let triangles = 0;
  let vertices = 0;
  scene.traverse((obj) => {
    if (!obj.isMesh) return;
    const position = obj.geometry.attributes.position;
    const vertexCount = position ? position.count : 0;
    vertices += vertexCount;
    triangles += obj.geometry.index ? obj.geometry.index.count / 3 : vertexCount / 3;
  });
  return { triangles: Math.round(triangles), vertices };
}

function setWireframe(scene, value) {
  scene.traverse((obj) => {
    if (!obj.isMesh) return;
    const materials = Array.isArray(obj.material) ? obj.material : [obj.material];
    materials.forEach((material) => {
      material.wireframe = value;
    });
  });
}

function Model({ url, wireframe, onStats }) {
  const { scene } = useGLTF(url);

  useEffect(() => {
    onStats(countGeometry(scene));
  }, [scene]);

  useEffect(() => {
    setWireframe(scene, wireframe);
    // The loader caches scenes, so always leave them in normal rendering mode.
    return () => setWireframe(scene, false);
  }, [scene, wireframe]);

  return <primitive object={scene} />;
}

// Shows real download progress while the .glb is being fetched.
function Loader() {
  const { progress } = useProgress();
  return (
    <Html center>
      <span className="loader">Loading model {Math.round(progress)}%</span>
    </Html>
  );
}

export default function Viewer({ assetUrl }) {
  // Changing resetKey remounts the scene, which restores the default camera framing.
  const [resetKey, setResetKey] = useState(0);
  const [wireframe, setWireframeOn] = useState(false);
  const [autoRotate, setAutoRotate] = useState(false);
  const [stats, setStats] = useState(null);

  if (!assetUrl) {
    return (
      <div className="stage-message">
        <p className="muted">Your model will appear here.</p>
      </div>
    );
  }

  return (
    <div className="viewer">
      <ViewerErrorBoundary key={`${assetUrl}-${resetKey}`}>
        <Canvas camera={{ position: [2, 1.5, 3], fov: 45 }} dpr={[1, 2]}>
          <ambientLight intensity={0.7} />
          <directionalLight position={[5, 8, 5]} intensity={1.6} />
          <directionalLight position={[-4, 2, -3]} intensity={0.5} />
          <Suspense fallback={<Loader />}>
            {/* Bounds + Center auto-frame any model, whatever its size or origin. */}
            <Bounds fit clip observe margin={1.3}>
              <Center>
                <Model url={assetUrl} wireframe={wireframe} onStats={setStats} />
              </Center>
            </Bounds>
          </Suspense>
          <OrbitControls makeDefault enableDamping autoRotate={autoRotate} autoRotateSpeed={2} />
        </Canvas>
      </ViewerErrorBoundary>

      {stats && (
        <p className="viewer-stats">
          {stats.triangles.toLocaleString()} triangles · {stats.vertices.toLocaleString()} vertices
        </p>
      )}

      <div className="viewer-actions">
        <button
          type="button"
          className="secondary"
          aria-pressed={autoRotate}
          onClick={() => setAutoRotate((v) => !v)}
        >
          Auto-rotate
        </button>
        <button
          type="button"
          className="secondary"
          aria-pressed={wireframe}
          onClick={() => setWireframeOn((v) => !v)}
        >
          Wireframe
        </button>
        <button type="button" className="secondary" onClick={() => setResetKey((k) => k + 1)}>
          Reset view
        </button>
        <a className="secondary" href={assetUrl} download target="_blank" rel="noreferrer">
          Download .glb
        </a>
      </div>
    </div>
  );
}
