import { Canvas, useFrame } from "@react-three/fiber";
import { OrbitControls, Html, useTexture } from "@react-three/drei";
import { useRef, useState } from "react";
import "./EarthSelector.css";

const countries = [
  { name: "대한민국", lat: 37.5665, lng: 126.978 },
  { name: "미국", lat: 38.9072, lng: -77.0369 },
  { name: "중국", lat: 39.9042, lng: 116.4074 },
];

function latLngToVector3(lat, lng, radius = 2.08) {
  const phi = (90 - lat) * (Math.PI / 180);
  const theta = (lng + 180) * (Math.PI / 180);

  const x = -radius * Math.sin(phi) * Math.cos(theta);
  const y = radius * Math.cos(phi);
  const z = radius * Math.sin(phi) * Math.sin(theta);

  return [x, y, z];
}

function CountryPin({ country, onSelect }) {
  const [hovered, setHovered] = useState(false);
  const position = latLngToVector3(country.lat, country.lng);

  return (
    <group position={position}>
      <mesh
        scale={hovered ? 0.1 : 0.07}
        onPointerEnter={(e) => {
          e.stopPropagation();
          setHovered(true);
        }}
        onPointerLeave={(e) => {
          e.stopPropagation();
          setHovered(false);
        }}
        onClick={(e) => {
          e.stopPropagation();
          onSelect(country);
        }}
      >
        <sphereGeometry args={[1, 24, 24]} />
        <meshBasicMaterial color="#ff5a5a" />
      </mesh>

      {hovered && (
        <Html center distanceFactor={8}>
          <div className="country-tooltip">{country.name}</div>
        </Html>
      )}
    </group>
  );
}

function Globe({ onSelectCountry }) {
  const globeRef = useRef();
  const [hovered, setHovered] = useState(false);
  const earthTexture = useTexture("/earth.jpg");

  useFrame((state, delta) => {
    if (!hovered && globeRef.current) {
      globeRef.current.rotation.y += delta * 0.15;
    }
  });

  return (
    <group ref={globeRef}>
      <mesh
        onPointerEnter={() => setHovered(true)}
        onPointerLeave={() => setHovered(false)}
      >
        <sphereGeometry args={[2, 64, 64]} />
        <meshStandardMaterial map={earthTexture} roughness={1} />
      </mesh>

      {hovered &&
        countries.map((country) => (
          <CountryPin
            key={country.name}
            country={country}
            onSelect={onSelectCountry}
          />
        ))}
    </group>
  );
}

export default function EarthSelector() {
  const [selectedCountry, setSelectedCountry] = useState(null);

  const handleYesClick = () => {
    alert(`${selectedCountry.name} 선택 완료`);
    setSelectedCountry(null);
  };

  return (
    <div className="earth-page">
      <h2 className="earth-title">국가를 선택해주세요</h2>
      <p className="earth-guide">
        드래그해서 지구를 돌리고, 국가 포인터를 선택해보세요
      </p>

      <div className="earth-box">
        <Canvas camera={{ position: [0, 0, 5.5], fov: 45 }}>
          <ambientLight intensity={1.5} />
          <directionalLight position={[4, 4, 5]} intensity={1.5} />

          <Globe onSelectCountry={setSelectedCountry} />

          <OrbitControls
            enablePan={false}
            enableZoom={false}
            rotateSpeed={0.6}
          />
        </Canvas>
      </div>

      {selectedCountry && (
        <div className="modal-backdrop">
          <div className="select-modal">
            <p>
              <b>{selectedCountry.name}</b>을 선택하시겠습니까?
            </p>

            <div className="modal-buttons">
              <button className="yes-button" onClick={handleYesClick}>
                YES
              </button>

              <button
                className="no-button"
                onClick={() => setSelectedCountry(null)}
              >
                NO
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
