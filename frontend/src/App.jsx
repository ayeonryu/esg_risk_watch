import { useState } from "react";
import EarthSelector from "./components/mainPage/EarthSelector";
import ESGDashboard from "./components/Dashboard/ESGDashboard";

export default function App() {
  const [selectedCountry, setSelectedCountry] = useState(null);

  return (
    <>
      {selectedCountry ? (
        <ESGDashboard
          country={selectedCountry}
          onBack={() => setSelectedCountry(null)}
        />
      ) : (
        <EarthSelector onCountryConfirm={setSelectedCountry} />
      )}
    </>
  );
}
