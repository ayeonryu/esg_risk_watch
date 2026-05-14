import { useState, useEffect } from "react";

// 데이터 섹션
const newsItems = [
    "삼성전자, 탄소중립 2050 로드맵 발표 — 재생에너지 전환 가속화",
    "SK하이닉스 ESG 위원회 신설, 이사회 내 지속가능경영 강화",
    "현대차그룹, 협력사 ESG 평가 시스템 도입 — 공급망 관리 강화",
];

const keyIndicators = [
    { label: "탄소 배출량", value: "+15%", color: "#4CAF50", alert: true },
    { label: "재생에너지 비율", value: "38%", color: "#4CAF50" },
    { label: "여성 임원 비율", value: "22%", color: "#4CAF50" },
];

const riskSignalsData = [
    { label: "탄소 초과", level: "high" },
    { label: "공급망 리스크", level: "medium" },
    { label: "규정 위반", level: "high" },
];

const esgScores = { E: 55.5, S: 77.7, G: 33.3 };
const esgColors = { E: "#4CAF50", S: "#2196F3", G: "#9C27B0" };
const TABS = ["ALL", "E", "S", "G"];

export default function ESGDashboard() {
    const [activeTab, setActiveTab] = useState("ALL");
    const [isMobile, setIsMobile] = useState(window.innerWidth <= 768);

    useEffect(() => {
        const handleResize = () => setIsMobile(window.innerWidth <= 768);
        window.addEventListener("resize", handleResize);
        return () => window.removeEventListener("resize", handleResize);
    }, []);

    const filteredScores =
        activeTab === "ALL"
            ? esgScores
            : { [activeTab]: esgScores[activeTab] };

    return (
        <div style={{
            fontFamily: "'Noto Sans KR', 'Apple SD Gothic Neo', sans-serif",
            background: "#F5F7FA",
            minHeight: "100vh",
            width: "100%",
            margin: "0",
            padding: "0",
        }}>
            <div style={{
                background: "#fff",
                padding: "14px 16px 10px",
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                borderBottom: "1px solid #E8EAF0",
                position: "sticky",
                top: 0,
                zIndex: 10,
            }}>
                <button style={{ background: "none", border: "none", fontSize: 20, cursor: "pointer", color: "#555", padding: "0 4px" }}>‹</button>

                <div style={{ display: "flex", alignItems: "center", gap: 4, marginLeft: "auto" }}>
                    {TABS.map(tab => (
                        <button
                            key={tab}
                            onClick={() => setActiveTab(tab)}
                            style={{
                                background: activeTab === tab ? "#1A237E" : "none",
                                color: activeTab === tab ? "#fff" : "#888",
                                border: "none",
                                borderRadius: 4,
                                padding: "2px 7px",
                                fontSize: 11,
                                fontWeight: activeTab === tab ? 700 : 400,
                                cursor: "pointer",
                                transition: "all 0.15s",
                            }}
                        >
                            {tab}
                        </button>
                    ))}
                    <button style={{
                        background: "none", border: "1px solid #D0D4E0",
                        borderRadius: 4, padding: "2px 6px", cursor: "pointer",
                        fontSize: 12, color: "#888", marginLeft: 2,
                    }}>📅</button>
                    <span style={{ fontSize: 11, fontWeight: 700, color: "#1A237E", letterSpacing: 1, marginLeft: 6 }}>KOREA</span>
                </div>
            </div>

            {/* Scrollable Content */}
            <div style={{
                padding: "14px 14px 40px",
                display: "flex",
                flexDirection: "column",
                gap: 12,
                maxWidth: "1400px",
                margin: "0 auto"
            }}>

                {/* 핵심 뉴스 */}
                <Card title="핵심 뉴스">
                    <ul style={{ margin: 0, paddingLeft: 18, display: "flex", flexDirection: "column", gap: 8 }}>
                        {newsItems.map((item, i) => (
                            <li key={i} style={{ fontSize: 13, color: "#333", lineHeight: 1.6 }}>{item}</li>
                        ))}
                    </ul>
                </Card>

                {/* 주요 변동 지표 + ESG 바 차트 */}
                <div style={{
                    display: "grid",
                    gridTemplateColumns: isMobile ? "1fr" : "1fr 1.6fr",
                    gap: 12
                }}>
                    <Card title="주요 변동 지표" style={{ padding: "12px 10px" }}>
                        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                            {keyIndicators.map((ind, i) => (
                                <div key={i} style={{
                                    background: "#E8F5E9", color: "#2E7D32",
                                    borderRadius: 20, padding: "3px 10px",
                                    fontSize: 11, fontWeight: 600,
                                    display: "inline-block",
                                    textAlign: "center"
                                }}>
                                    {ind.label} {ind.value}
                                </div>
                            ))}
                        </div>
                    </Card>

                    <Card title="ESG 점수" style={{ padding: "12px 10px" }}>
                        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                            {Object.entries(filteredScores).map(([key, val]) => (
                                <div key={key}>
                                    <div style={{ display: "flex", justifyContent: "space-between", fontSize: 12, marginBottom: 3 }}>
                                        <span style={{ fontWeight: 700, color: esgColors[key] }}>{key}</span>
                                        <span style={{ fontWeight: 600, color: "#333" }}>{val}%</span>
                                    </div>
                                    <div style={{ background: "#E8EAF0", borderRadius: 0, height: 14, overflow: "hidden" }}>
                                        <div style={{
                                            width: `${val}%`,
                                            height: "100%",
                                            background: esgColors[key],
                                            borderRadius: 0,
                                            transition: "width 0.6s ease",
                                        }} />
                                    </div>
                                </div>
                            ))}
                        </div>
                    </Card>
                </div>

                {/* 하단 3 패널: PC에서는 가로 3열, 모바일은 세로 */}
                <div style={{
                    display: "grid",
                    gridTemplateColumns: isMobile ? "1fr" : "1fr 1fr 1fr",
                    gap: 10
                }}>
                    <StatCard label="ESG 종합 점수" value="77.7%" valueColor="#1A237E" />
                    <StatCard label="전월 대비 변화" value="+3.3%" valueColor="#2E7D32" />

                    {/* 위험 신호 */}
                    <Card style={{ padding: "10px 10px", display: "flex", flexDirection: "column", gap: 6 }}>
                        <p style={{ fontSize: 11, color: "#888", margin: "0 0 4px", fontWeight: 500 }}>위험 신호</p>
                        <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                            {riskSignalsData.map((sig, i) => (
                                <div key={i} style={{
                                    background: sig.level === "high" ? "#FFCDD2" : "#FFF9C4",
                                    color: sig.level === "high" ? "#C62828" : "#F57F17",
                                    borderRadius: 20, padding: "3px 10px",
                                    fontSize: 11, fontWeight: 600,
                                    display: "inline-block",
                                    textAlign: "center"
                                }}>
                                    {sig.label}
                                </div>
                            ))}
                        </div>
                    </Card>
                </div>

            </div>
        </div>
    );
}

function Card({ title, children, style = {} }) {
    return (
        <div style={{
            background: "#fff",
            borderRadius: 14,
            padding: "12px 14px",
            border: "1px solid #E8EAF0",
            boxShadow: "0 2px 4px rgba(0,0,0,0.02)",
            ...style,
        }}>
            {title && (
                <p style={{ fontSize: 12, fontWeight: 700, color: "#888", margin: "0 0 10px", letterSpacing: 0.3 }}>{title}</p>
            )}
            {children}
        </div>
    );
}

function StatCard({ label, value, valueColor }) {
    return (
        <Card style={{ padding: "10px 10px", textAlign: "center" }}>
            <p style={{ fontSize: 11, color: "#888", margin: "0 0 6px", fontWeight: 500 }}>{label}</p>
            <p style={{ fontSize: 20, fontWeight: 700, color: valueColor || "#1A237E", margin: 0 }}>{value}</p>
        </Card>
    );
}