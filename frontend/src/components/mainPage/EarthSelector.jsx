import { Canvas, useFrame } from "@react-three/fiber";
import { OrbitControls, Html, useTexture } from "@react-three/drei";
import { useEffect, useRef, useState } from "react";
import "./EarthSelector.css";

const countries = [
  { name: "대한민국", code: "KOR", lat: 37.5665, lng: 126.978 },
  { name: "미국", code: "USA", lat: 38.9072, lng: -77.0369 },
  { name: "중국", code: "CHN", lat: 39.9042, lng: 116.4074 },
  { name: "독일", code: "DEU", lat: 52.52, lng: 13.405 },
];

function latLngToVector3(lat, lng, radius = 2.15) {
  const phi = (90 - lat) * (Math.PI / 180);
  const theta = (lng + 180) * (Math.PI / 180);

  const x = -radius * Math.sin(phi) * Math.cos(theta);
  const y = radius * Math.cos(phi);
  const z = radius * Math.sin(phi) * Math.sin(theta);

  return [x, y, z];
}

function CountryPin({
  country,
  visible,
  hoveredCountry,
  setHoveredCountry,
  onSelect,
  clearHoverLater,
  cancelClearHover,
}) {
  const position = latLngToVector3(country.lat, country.lng);
  const isHovered = hoveredCountry?.name === country.name;

  const handlePointerOver = (e) => {
    e.stopPropagation();
    cancelClearHover();

    setHoveredCountry((prev) => {
      if (prev?.name === country.name) return prev;
      return country;
    });
  };

  const handlePointerOut = (e) => {
    e.stopPropagation();
    clearHoverLater(country);
  };

  const handleSelect = (e) => {
    e.stopPropagation();
    cancelClearHover();
    setHoveredCountry(country);
    onSelect(country);
  };

  return (
    <group position={position} visible={visible}>
      {/* 실제로 보이는 빨간 점 */}
      <mesh
        scale={isHovered ? 0.13 : 0.09}
        onPointerOver={handlePointerOver}
        onPointerOut={handlePointerOut}
        onPointerDown={handleSelect}
      >
        <sphereGeometry args={[1, 24, 24]} />
        <meshBasicMaterial color="#ff6961" />
      </mesh>

      {/* 클릭 범위를 넓히기 위한 투명 영역 */}
      <mesh
        scale={0.4}
        onPointerOver={handlePointerOver}
        onPointerOut={handlePointerOut}
        onPointerDown={handleSelect}
      >
        <sphereGeometry args={[1, 24, 24]} />
        <meshBasicMaterial transparent opacity={0} depthWrite={false} />
      </mesh>

      {/* 나라 이름: hover 중일 때만 표시 */}
      {visible && isHovered && (
        <Html
          center
          position={[0, 0.22, 0]}
          zIndexRange={[100, 0]}
          style={{
            pointerEvents: "none",
          }}
        >
          <div className="country-tooltip">{country.name}</div>
        </Html>
      )}
    </group>
  );
}

function Globe({ onSelectCountry, active }) {
  const globeRef = useRef();
  const hoverClearTimerRef = useRef(null);

  const [hoveredCountry, setHoveredCountry] = useState(null);

  const earthTexture = useTexture("/earth.jpg");

  const cancelClearHover = () => {
    if (hoverClearTimerRef.current) {
      clearTimeout(hoverClearTimerRef.current);
      hoverClearTimerRef.current = null;
    }
  };

  const clearHoverLater = (country) => {
    cancelClearHover();

    hoverClearTimerRef.current = setTimeout(() => {
      setHoveredCountry((prev) => {
        if (prev?.name === country.name) {
          return null;
        }
        return prev;
      });
    }, 120);
  };

  useEffect(() => {
    if (!active) {
      cancelClearHover();
      const timer = setTimeout(() => setHoveredCountry(null), 0);
      return () => clearTimeout(timer);
    }
  }, [active]);

  useEffect(() => {
    return () => {
      cancelClearHover();
    };
  }, []);

  useFrame((state, delta) => {
    if (!active && globeRef.current) {
      globeRef.current.rotation.y += delta * 0.15;
    }
  });

  return (
    <group ref={globeRef}>
      {/* 지구 */}
      <mesh>
        <sphereGeometry args={[2, 64, 64]} />
        <meshStandardMaterial map={earthTexture} roughness={1} />
      </mesh>

      {/* 국가 핀 */}
      {countries.map((country) => (
        <CountryPin
          key={country.name}
          country={country}
          visible={active}
          hoveredCountry={hoveredCountry}
          setHoveredCountry={setHoveredCountry}
          onSelect={onSelectCountry}
          clearHoverLater={clearHoverLater}
          cancelClearHover={cancelClearHover}
        />
      ))}
    </group>
  );
}

export default function EarthSelector({ onCountryConfirm }) {
  const [selectedCountry, setSelectedCountry] = useState(null);
  const [isEarthHovered, setIsEarthHovered] = useState(false);

  const handleYesClick = () => {
    if (selectedCountry) {
      onCountryConfirm(selectedCountry);
    }
  };

  return (
    <div className="earth-page">
      <h2 className="earth-title">국가를 선택해주세요</h2>

      <p className="earth-guide">
        드래그해서 지구를 돌리고, 국가 포인터를 선택해보세요
      </p>

      <div
        className="earth-box"
        onPointerEnter={() => setIsEarthHovered(true)}
        onPointerLeave={() => setIsEarthHovered(false)}
      >
        <Canvas camera={{ position: [0, 0, 5.5], fov: 45 }}>
          <ambientLight intensity={1.5} />
          <directionalLight position={[4, 4, 5]} intensity={1.5} />

          <Globe onSelectCountry={setSelectedCountry} active={isEarthHovered} />

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
