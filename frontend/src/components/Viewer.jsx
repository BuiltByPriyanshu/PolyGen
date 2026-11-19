import { Suspense, useState } from "react";
import { Canvas } from "@react-three/fiber";
import { Bounds, Center, Html, OrbitControls, useGLTF, useProgress } from "@react-three/drei";
import ViewerErrorBoundary from "./ViewerErrorBoundary.jsx";

function Model({ url }) {
  const { scene } = useGLTF(url);
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
                <Model url={assetUrl} />
              </Center>
            </Bounds>
          </Suspense>
          <OrbitControls makeDefault enableDamping />
        </Canvas>
      </ViewerErrorBoundary>

      <div className="viewer-actions">
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
