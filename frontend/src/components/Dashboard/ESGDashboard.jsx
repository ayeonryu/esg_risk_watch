import { useState, useEffect } from "react";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api/v1";

const COUNTRY_CODE_BY_NAME = {
  대한민국: "KOR",
  미국: "USA",
  중국: "CHN",
  독일: "DEU",
};

const esgColors = { E: "#4CAF50", S: "#2196F3", G: "#9C27B0" };
const esgLabels = { E: "환경", S: "사회", G: "지배구조" };
const TABS = ["ALL", "E", "S", "G"];

function addDateRangeParams(params, startDate, endDate) {
  if (startDate) {
    params.set("start_date", startDate);
  }
  if (endDate) {
    params.set("end_date", endDate);
  }
}

function hasNumericValue(value) {
  if (value === null || value === undefined || value === "") {
    return false;
  }
  return Number.isFinite(Number(value));
}

function formatIndicatorValue(item) {
  if (item.change_pct !== null && item.change_pct !== undefined) {
    const sign = item.direction === "up" ? "+" : item.direction === "down" ? "-" : "";
    return `${sign}${Math.abs(item.change_pct).toFixed(1)}%`;
  }

  const value = Number(item.value);
  if (!Number.isFinite(value)) {
    return "-";
  }

  const formatted = value.toLocaleString("ko-KR", {
    maximumFractionDigits: 1,
  });
  return item.unit ? `${formatted} ${item.unit}` : formatted;
}

function indicatorColor(riskLevel) {
  if (riskLevel === "high") {
    return "#C62828";
  }
  if (riskLevel === "medium") {
    return "#F57F17";
  }
  return "#2E7D32";
}

function formatScoreValue(value) {
  if (!hasNumericValue(value)) {
    return "데이터 없음";
  }
  const number = Number(value);
  return `${number.toFixed(1)}%`;
}

function formatScoreChange(value) {
  if (!hasNumericValue(value)) {
    return "데이터 없음";
  }
  const number = Number(value);
  const sign = number > 0 ? "+" : "";
  return `${sign}${number.toFixed(1)}%`;
}

function scoreChangeColor(value) {
  if (!hasNumericValue(value)) {
    return "#777";
  }
  const number = Number(value);
  return number < 0 ? "#C62828" : "#2E7D32";
}

export default function ESGDashboard({ country, onBack }) {
  const [activeTab, setActiveTab] = useState("ALL");
  const [isMobile, setIsMobile] = useState(() => window.innerWidth <= 768);

  const [isCalendarOpen, setIsCalendarOpen] = useState(false);
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [appliedStartDate, setAppliedStartDate] = useState("");
  const [appliedEndDate, setAppliedEndDate] = useState("");
  const [dateError, setDateError] = useState("");
  const [newsItems, setNewsItems] = useState([]);
  const [newsStatus, setNewsStatus] = useState("idle");
  const [indicatorItems, setIndicatorItems] = useState([]);
  const [indicatorStatus, setIndicatorStatus] = useState("idle");
  const [riskSignalItems, setRiskSignalItems] = useState([]);
  const [riskSignalStatus, setRiskSignalStatus] = useState("idle");
  const [scoreItems, setScoreItems] = useState({});
  const [previousScoreItems, setPreviousScoreItems] = useState({});
  const [scoreChanges, setScoreChanges] = useState({});
  const [scoreSummary, setScoreSummary] = useState({
    overall: null,
    previousOverall: null,
    overallChange: null,
  });
  const [scoreStatus, setScoreStatus] = useState("idle");
  const [scoreTrendItems, setScoreTrendItems] = useState([]);
  const [scoreTrendStatus, setScoreTrendStatus] = useState("idle");

  const countryName = country?.name || "선택 국가";
  const countryCode = country?.code || COUNTRY_CODE_BY_NAME[countryName];

  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth <= 768);
    window.addEventListener("resize", handleResize);

    return () => window.removeEventListener("resize", handleResize);
  }, []);

  useEffect(() => {
    const controller = new AbortController();

    async function loadNews() {
      setNewsStatus("loading");

      try {
        const params = new URLSearchParams({ limit: "5" });
        if (countryCode) {
          params.set("country", countryCode);
        }
        addDateRangeParams(params, appliedStartDate, appliedEndDate);

        const response = await fetch(`${API_BASE_URL}/news/?${params}`, {
          signal: controller.signal,
        });

        if (!response.ok) {
          throw new Error(`News API failed: ${response.status}`);
        }

        const data = await response.json();
        setNewsItems(
          data.map((item) => ({
            title: item.title,
            media: item.media,
            publishedAt: item.published_at,
            url: item.url,
          })),
        );
        setNewsStatus(data.length > 0 ? "loaded" : "empty");
      } catch (error) {
        if (error.name !== "AbortError") {
          console.warn(error);
          setNewsItems([]);
          setNewsStatus("error");
        }
      }
    }

    loadNews();

    return () => controller.abort();
  }, [countryCode, appliedStartDate, appliedEndDate]);

  useEffect(() => {
    const controller = new AbortController();

    async function loadScoreTrend() {
      setScoreTrendStatus("loading");

      try {
        const params = new URLSearchParams({ limit: "6" });
        if (countryCode) {
          params.set("country", countryCode);
        }
        addDateRangeParams(params, appliedStartDate, appliedEndDate);

        const response = await fetch(`${API_BASE_URL}/indicators/score-trend?${params}`, {
          signal: controller.signal,
        });

        if (!response.ok) {
          throw new Error(`Score trend API failed: ${response.status}`);
        }

        const data = await response.json();
        const items = data.items || [];
        setScoreTrendItems(items);
        setScoreTrendStatus(items.length > 0 ? "loaded" : "empty");
      } catch (error) {
        if (error.name !== "AbortError") {
          console.warn(error);
          setScoreTrendItems([]);
          setScoreTrendStatus("error");
        }
      }
    }

    loadScoreTrend();

    return () => controller.abort();
  }, [countryCode, appliedStartDate, appliedEndDate]);

  useEffect(() => {
    const controller = new AbortController();

    async function loadIndicators() {
      setIndicatorStatus("loading");
      setRiskSignalStatus("loading");

      try {
        const params = new URLSearchParams({ limit: "4" });
        if (countryCode) {
          params.set("country", countryCode);
        }
        addDateRangeParams(params, appliedStartDate, appliedEndDate);

        const response = await fetch(`${API_BASE_URL}/indicators/summary?${params}`, {
          signal: controller.signal,
        });

        if (!response.ok) {
          throw new Error(`Indicators API failed: ${response.status}`);
        }

        const data = await response.json();
        const items = data.items || [];
        setIndicatorItems(
          items.length > 0
            ? items.map((item) => ({
                label: item.label,
                value: formatIndicatorValue(item),
                category: item.category,
                color: indicatorColor(item.risk_level),
              }))
            : [],
        );
        setRiskSignalItems(
          items
            .filter((item) => ["high", "medium"].includes(item.risk_level))
            .map((item) => ({
              label: `${item.label} ${formatIndicatorValue(item)}`,
              level: item.risk_level,
              category: item.category,
            })),
        );
        setIndicatorStatus(items.length > 0 ? "loaded" : "empty");
        setRiskSignalStatus(
          items.length === 0
            ? "empty"
            : items.some((item) => ["high", "medium"].includes(item.risk_level))
              ? "loaded"
              : "no-risk",
        );
      } catch (error) {
        if (error.name !== "AbortError") {
          console.warn(error);
          setIndicatorItems([]);
          setIndicatorStatus("error");
          setRiskSignalItems([]);
          setRiskSignalStatus("error");
        }
      }
    }

    loadIndicators();

    return () => controller.abort();
  }, [countryCode, appliedStartDate, appliedEndDate]);

  useEffect(() => {
    const controller = new AbortController();

    async function loadScores() {
      setScoreStatus("loading");

      try {
        const params = new URLSearchParams();
        if (countryCode) {
          params.set("country", countryCode);
        }
        addDateRangeParams(params, appliedStartDate, appliedEndDate);

        const response = await fetch(`${API_BASE_URL}/indicators/scores?${params}`, {
          signal: controller.signal,
        });

        if (!response.ok) {
          throw new Error(`Scores API failed: ${response.status}`);
        }

        const data = await response.json();
        const scores = data.scores || {};
        setScoreItems(scores);
        setPreviousScoreItems(data.previous_scores || {});
        setScoreChanges(data.score_changes || {});
        setScoreSummary({
          overall: data.overall,
          previousOverall: data.previous_overall,
          overallChange: data.overall_change,
        });
        setScoreStatus(Object.keys(scores).length > 0 ? "loaded" : "empty");
      } catch (error) {
        if (error.name !== "AbortError") {
          console.warn(error);
          setScoreItems({});
          setPreviousScoreItems({});
          setScoreChanges({});
          setScoreSummary({ overall: null, previousOverall: null, overallChange: null });
          setScoreStatus("error");
        }
      }
    }

    loadScores();

    return () => controller.abort();
  }, [countryCode, appliedStartDate, appliedEndDate]);

  const handleStartDateChange = (e) => {
    const newStartDate = e.target.value;
    setStartDate(newStartDate);
    setDateError("");

    if (endDate && endDate < newStartDate) {
      setEndDate(newStartDate);
    }
  };

  const handleEndDateChange = (e) => {
    setEndDate(e.target.value);
    setDateError("");
  };

  const handleApplyDateRange = () => {
    if (!startDate || !endDate) {
      setDateError("시작일과 종료일을 모두 선택해주세요.");
      return;
    }
    if (startDate > endDate) {
      setDateError("시작일은 종료일보다 늦을 수 없습니다.");
      return;
    }

    setAppliedStartDate(startDate);
    setAppliedEndDate(endDate);
    setDateError("");
    setIsCalendarOpen(false);
  };

  const handleClearDateRange = () => {
    setStartDate("");
    setEndDate("");
    setAppliedStartDate("");
    setAppliedEndDate("");
    setDateError("");
    setIsCalendarOpen(false);
  };

  const filteredScores =
    activeTab === "ALL"
      ? scoreItems
      : scoreItems[activeTab] !== undefined
        ? { [activeTab]: scoreItems[activeTab] }
        : {};
  const filteredIndicatorItems =
    activeTab === "ALL"
      ? indicatorItems
      : indicatorItems.filter((item) => item.category === activeTab);
  const filteredRiskSignalItems =
    activeTab === "ALL"
      ? riskSignalItems
      : riskSignalItems.filter((item) => item.category === activeTab);
  const selectedScoreLabel =
    activeTab === "ALL" ? "ESG 종합" : `${activeTab} ${esgLabels[activeTab]}`;
  const selectedScore =
    activeTab === "ALL" ? scoreSummary.overall : scoreItems[activeTab];
  const selectedPreviousScore =
    activeTab === "ALL" ? scoreSummary.previousOverall : previousScoreItems[activeTab];
  const selectedScoreChange =
    activeTab === "ALL" ? scoreSummary.overallChange : scoreChanges[activeTab];
  const selectedScoreColor =
    activeTab === "ALL" ? "#1A237E" : esgColors[activeTab] || "#1A237E";

  return (
    <div
      style={{
        fontFamily: "'Noto Sans KR', 'Apple SD Gothic Neo', sans-serif",
        background: "#F5F7FA",
        minHeight: "100vh",
        width: "100%",
        margin: "0",
        padding: "0",
      }}
    >
      {/* 상단바 */}
      <div
        style={{
          background: "#fff",
          padding: "14px 16px 10px",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          borderBottom: "1px solid #E8EAF0",
          position: "sticky",
          top: 0,
          zIndex: 10,
        }}
      >
        <button
          onClick={onBack}
          style={{
            background: "none",
            border: "none",
            fontSize: 24,
            cursor: "pointer",
            color: "#555",
            padding: "0 4px",
          }}
        >
          ‹
        </button>

        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 4,
            marginLeft: "auto",
            position: "relative",
          }}
        >
          {TABS.map((tab) => (
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

          {/* 달력 버튼 */}
          <button
            onClick={() => setIsCalendarOpen((prev) => !prev)}
            style={{
              background: "none",
              border: "1px solid #D0D4E0",
              borderRadius: 4,
              padding: "2px 6px",
              cursor: "pointer",
              fontSize: 12,
              color: "#888",
              marginLeft: 2,
            }}
          >
            📅
          </button>

          {/* 선택한 나라 이름 */}
          <span
            style={{
              fontSize: 11,
              fontWeight: 700,
              color: "#1A237E",
              letterSpacing: 1,
              marginLeft: 6,
              whiteSpace: "nowrap",
            }}
          >
            {countryName}
          </span>

          {/* 기간 선택 팝업 */}
          {isCalendarOpen && (
            <div
              style={{
                position: "absolute",
                top: 34,
                right: 0,
                background: "#fff",
                border: "1px solid #D0D4E0",
                borderRadius: 12,
                padding: 14,
                boxShadow: "0 8px 24px rgba(0,0,0,0.14)",
                zIndex: 30,
                width: 260,
              }}
            >
              <p
                style={{
                  margin: "0 0 12px",
                  fontSize: 13,
                  fontWeight: 700,
                  color: "#1A237E",
                }}
              >
                기간 선택
              </p>

              <div
                style={{
                  display: "flex",
                  flexDirection: "column",
                  gap: 10,
                }}
              >
                <div>
                  <p
                    style={{
                      margin: "0 0 5px",
                      fontSize: 11,
                      color: "#666",
                      fontWeight: 600,
                    }}
                  >
                    시작일
                  </p>

                  <input
                    type="date"
                    value={startDate}
                    onChange={handleStartDateChange}
                    style={{
                      width: "100%",
                      boxSizing: "border-box",
                      border: "1px solid #D0D4E0",
                      borderRadius: 7,
                      padding: "7px 8px",
                      fontSize: 12,
                    }}
                  />
                </div>

                <div>
                  <p
                    style={{
                      margin: "0 0 5px",
                      fontSize: 11,
                      color: "#666",
                      fontWeight: 600,
                    }}
                  >
                    종료일
                  </p>

                  <input
                    type="date"
                    value={endDate}
                    min={startDate}
                    onChange={handleEndDateChange}
                    style={{
                      width: "100%",
                      boxSizing: "border-box",
                      border: "1px solid #D0D4E0",
                      borderRadius: 7,
                      padding: "7px 8px",
                      fontSize: 12,
                    }}
                  />
                </div>
              </div>

              <p
                style={{
                  margin: "12px 0 0",
                  fontSize: 11,
                  color: "#777",
                  lineHeight: 1.5,
                }}
              >
                적용 기간:{" "}
                {appliedStartDate && appliedEndDate
                  ? `${appliedStartDate} ~ ${appliedEndDate}`
                  : "전체 기간"}
              </p>

              {dateError && (
                <p
                  style={{
                    margin: "8px 0 0",
                    color: "#C62828",
                    fontSize: 11,
                    fontWeight: 600,
                  }}
                >
                  {dateError}
                </p>
              )}

              <button
                onClick={handleApplyDateRange}
                style={{
                  width: "100%",
                  marginTop: 12,
                  padding: "8px 0",
                  border: "none",
                  borderRadius: 7,
                  background: "#1A237E",
                  color: "#fff",
                  fontSize: 12,
                  fontWeight: 700,
                  cursor: "pointer",
                }}
              >
                적용
              </button>

              <button
                onClick={handleClearDateRange}
                style={{
                  width: "100%",
                  marginTop: 7,
                  padding: "8px 0",
                  border: "1px solid #D0D4E0",
                  borderRadius: 7,
                  background: "#fff",
                  color: "#555",
                  fontSize: 12,
                  fontWeight: 700,
                  cursor: "pointer",
                }}
              >
                전체 기간
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Scrollable Content */}
      <div
        style={{
          padding: "14px 14px 40px",
          display: "flex",
          flexDirection: "column",
          gap: 12,
          maxWidth: "1400px",
          margin: "0 auto",
        }}
      >
        <Card title="핵심 뉴스">
          <ul
            style={{
              margin: 0,
              paddingLeft: 18,
              display: "flex",
              flexDirection: "column",
              gap: 8,
            }}
          >
            {newsStatus === "loading" && (
              <li
                style={{
                  fontSize: 13,
                  color: "#777",
                  lineHeight: 1.6,
                }}
              >
                뉴스를 불러오는 중입니다...
              </li>
            )}

            {newsStatus === "empty" && (
              <li style={{ fontSize: 13, color: "#777", lineHeight: 1.6 }}>
                실제 뉴스 데이터가 없습니다.
              </li>
            )}

            {newsStatus === "error" && (
              <li style={{ fontSize: 13, color: "#C62828", lineHeight: 1.6 }}>
                실제 뉴스 데이터를 불러오지 못했습니다.
              </li>
            )}

            {newsItems.map((item, i) => (
              <li
                key={i}
                style={{
                  fontSize: 13,
                  color: "#333",
                  lineHeight: 1.6,
                }}
              >
                {typeof item === "string" || !item.url ? (
                  typeof item === "string" ? item : item.title
                ) : (
                  <a
                    href={item.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{
                      color: "inherit",
                      textDecoration: "underline",
                      textUnderlineOffset: 2,
                    }}
                  >
                    {item.title}
                  </a>
                )}
                {typeof item !== "string" && (item.media || item.publishedAt) && (
                  <span style={{ color: "#888", fontSize: 11 }}>
                    {" "}
                    · {[item.media, item.publishedAt].filter(Boolean).join(" · ")}
                  </span>
                )}
              </li>
            ))}
          </ul>
        </Card>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: isMobile ? "1fr" : "1fr 1.6fr",
            gap: 12,
          }}
        >
          <Card title="주요 변동 지표" style={{ padding: "12px 10px" }}>
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {indicatorStatus === "loading" && (
                <div
                  style={{
                    color: "#777",
                    fontSize: 11,
                    fontWeight: 600,
                    padding: "3px 10px",
                  }}
                >
                  지표를 불러오는 중입니다...
                </div>
              )}

              {indicatorStatus === "empty" && (
                <div
                  style={{
                    color: "#777",
                    fontSize: 11,
                    fontWeight: 600,
                    padding: "3px 10px",
                  }}
                >
                  실제 지표 데이터가 없습니다.
                </div>
              )}

              {indicatorStatus === "error" && (
                <div
                  style={{
                    color: "#C62828",
                    fontSize: 11,
                    fontWeight: 600,
                    padding: "3px 10px",
                  }}
                >
                  실제 지표 데이터를 불러오지 못했습니다.
                </div>
              )}

              {indicatorStatus === "loaded" && filteredIndicatorItems.length === 0 && (
                <div
                  style={{
                    color: "#777",
                    fontSize: 11,
                    fontWeight: 600,
                    padding: "3px 10px",
                  }}
                >
                  선택한 분야의 지표 데이터가 없습니다.
                </div>
              )}

              {filteredIndicatorItems.map((ind, i) => (
                <div
                  key={i}
                  style={{
                    background: "#E8F5E9",
                    color: ind.color || "#2E7D32",
                    borderRadius: 20,
                    padding: "3px 10px",
                    fontSize: 11,
                    fontWeight: 600,
                    display: "inline-block",
                    textAlign: "center",
                  }}
                >
                  {ind.label} {ind.value}
                </div>
              ))}
            </div>
          </Card>

          <Card title="ESG 점수" style={{ padding: "12px 10px" }}>
            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              {scoreStatus === "loading" && (
                <div style={{ color: "#777", fontSize: 11, fontWeight: 600 }}>
                  ESG 점수를 불러오는 중입니다...
                </div>
              )}

              {scoreStatus === "empty" && (
                <div style={{ color: "#777", fontSize: 11, fontWeight: 600 }}>
                  실제 ESG 점수 데이터가 없습니다.
                </div>
              )}

              {scoreStatus === "error" && (
                <div style={{ color: "#C62828", fontSize: 11, fontWeight: 600 }}>
                  실제 ESG 점수를 불러오지 못했습니다.
                </div>
              )}

              {scoreStatus === "loaded" && Object.keys(filteredScores).length === 0 && (
                <div style={{ color: "#777", fontSize: 11, fontWeight: 600 }}>
                  선택한 분야의 ESG 점수 데이터가 없습니다.
                </div>
              )}

              {Object.entries(filteredScores).map(([key, val]) => (
                <div key={key}>
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      fontSize: 12,
                      marginBottom: 3,
                    }}
                  >
                    <span style={{ fontWeight: 700, color: esgColors[key] }}>
                      {key} {esgLabels[key]}
                    </span>
                    <span style={{ fontWeight: 600, color: "#333" }}>
                      {formatScoreValue(val)}
                    </span>
                  </div>

                  <div
                    style={{
                      background: "#E8EAF0",
                      borderRadius: 0,
                      height: 14,
                      overflow: "hidden",
                    }}
                  >
                    <div
                      style={{
                        width: `${Number(val) || 0}%`,
                        height: "100%",
                        background: esgColors[key],
                        borderRadius: 0,
                        transition: "width 0.6s ease",
                      }}
                    />
                  </div>
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      color: "#777",
                      fontSize: 11,
                      marginTop: 4,
                    }}
                  >
                    <span>전년도 점수 {formatScoreValue(previousScoreItems[key])}</span>
                    <span
                      style={{
                        color: scoreChangeColor(scoreChanges[key]),
                        fontWeight: 700,
                      }}
                    >
                      전년도 대비 {formatScoreChange(scoreChanges[key])}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: isMobile ? "1fr" : "1fr 1fr 1fr",
            gap: 10,
          }}
        >
          <StatCard
            label={`${selectedScoreLabel} 점수`}
            value={formatScoreValue(selectedScore)}
            valueColor={selectedScoreColor}
            helper={`전년도 점수 ${formatScoreValue(selectedPreviousScore)}`}
          />
          <StatCard
            label="전년도 대비 변화"
            value={formatScoreChange(selectedScoreChange)}
            valueColor={scoreChangeColor(selectedScoreChange)}
          />

          <Card
            style={{
              padding: "10px 10px",
              display: "flex",
              flexDirection: "column",
              gap: 6,
            }}
          >
            <p
              style={{
                fontSize: 11,
                color: "#888",
                margin: "0 0 4px",
                fontWeight: 500,
              }}
            >
              위험 신호
            </p>

            <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
              {riskSignalStatus === "loading" && (
                <div style={{ color: "#777", fontSize: 11, fontWeight: 600 }}>
                  위험 신호를 불러오는 중입니다...
                </div>
              )}

              {riskSignalStatus === "empty" && (
                <div style={{ color: "#777", fontSize: 11, fontWeight: 600 }}>
                  실제 위험 신호 데이터가 없습니다.
                </div>
              )}

              {riskSignalStatus === "no-risk" && activeTab === "ALL" && (
                <div style={{ color: "#2E7D32", fontSize: 11, fontWeight: 600 }}>
                  현재 주요 위험 신호가 없습니다.
                </div>
              )}

              {riskSignalStatus === "loaded" && filteredRiskSignalItems.length === 0 && (
                <div style={{ color: "#2E7D32", fontSize: 11, fontWeight: 600 }}>
                  선택한 분야의 주요 위험 신호가 없습니다.
                </div>
              )}

              {riskSignalStatus === "no-risk" && activeTab !== "ALL" && (
                <div style={{ color: "#2E7D32", fontSize: 11, fontWeight: 600 }}>
                  선택한 분야의 주요 위험 신호가 없습니다.
                </div>
              )}

              {riskSignalStatus === "error" && (
                <div style={{ color: "#C62828", fontSize: 11, fontWeight: 600 }}>
                  실제 위험 신호를 불러오지 못했습니다.
                </div>
              )}

              {filteredRiskSignalItems.map((sig, i) => (
                <div
                  key={i}
                  style={{
                    background: sig.level === "high" ? "#FFCDD2" : "#FFF9C4",
                    color: sig.level === "high" ? "#C62828" : "#F57F17",
                    borderRadius: 20,
                    padding: "3px 10px",
                    fontSize: 11,
                    fontWeight: 600,
                    display: "inline-block",
                    textAlign: "center",
                  }}
                >
                  {sig.label}
                </div>
              ))}
            </div>
          </Card>
        </div>

        {activeTab === "ALL" && (
          <Card title="ESG 종합점수 추이" style={{ padding: "12px 10px" }}>
            {scoreTrendStatus === "loading" && (
              <div style={{ color: "#777", fontSize: 11, fontWeight: 600 }}>
                종합점수 추이를 불러오는 중입니다...
              </div>
            )}

            {scoreTrendStatus === "empty" && (
              <div style={{ color: "#777", fontSize: 11, fontWeight: 600 }}>
                종합점수 추이 데이터가 없습니다.
              </div>
            )}

            {scoreTrendStatus === "error" && (
              <div style={{ color: "#C62828", fontSize: 11, fontWeight: 600 }}>
                종합점수 추이를 불러오지 못했습니다.
              </div>
            )}

            {scoreTrendStatus === "loaded" && (
              <ScoreTrendChart items={scoreTrendItems} />
            )}
          </Card>
        )}
      </div>
    </div>
  );
}

function Card({ title, children, style = {} }) {
  return (
    <div
      style={{
        background: "#fff",
        borderRadius: 14,
        padding: "12px 14px",
        border: "1px solid #E8EAF0",
        boxShadow: "0 2px 4px rgba(0,0,0,0.02)",
        ...style,
      }}
    >
      {title && (
        <p
          style={{
            fontSize: 12,
            fontWeight: 700,
            color: "#888",
            margin: "0 0 10px",
            letterSpacing: 0.3,
          }}
        >
          {title}
        </p>
      )}

      {children}
    </div>
  );
}

function StatCard({ label, value, valueColor, helper }) {
  return (
    <Card style={{ padding: "10px 10px", textAlign: "center" }}>
      <p
        style={{
          fontSize: 11,
          color: "#888",
          margin: "0 0 6px",
          fontWeight: 500,
        }}
      >
        {label}
      </p>

      <p
        style={{
          fontSize: 20,
          fontWeight: 700,
          color: valueColor || "#1A237E",
          margin: 0,
        }}
      >
        {value}
      </p>

      {helper && (
        <p
          style={{
            fontSize: 10,
            color: "#888",
            margin: "5px 0 0",
            fontWeight: 600,
          }}
        >
          {helper}
        </p>
      )}
    </Card>
  );
}

function ScoreTrendChart({ items }) {
  const width = 640;
  const height = 190;
  const padding = { top: 18, right: 16, bottom: 34, left: 36 };
  const plotWidth = width - padding.left - padding.right;
  const plotHeight = height - padding.top - padding.bottom;
  const values = items.map((item) => Number(item.overall)).filter(Number.isFinite);

  if (items.length === 0 || values.length === 0) {
    return (
      <div style={{ color: "#777", fontSize: 11, fontWeight: 600 }}>
        종합점수 추이 데이터가 없습니다.
      </div>
    );
  }

  const points = items.map((item, index) => {
    const value = Number(item.overall);
    const x =
      padding.left +
      (items.length === 1 ? plotWidth / 2 : (plotWidth * index) / (items.length - 1));
    const y = padding.top + plotHeight - (Math.max(0, Math.min(100, value)) / 100) * plotHeight;
    return { ...item, value, x, y };
  });
  const linePoints = points.map((point) => `${point.x},${point.y}`).join(" ");
  const latest = points[points.length - 1];

  return (
    <div style={{ width: "100%", overflow: "hidden" }}>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "baseline",
          marginBottom: 8,
          gap: 10,
        }}
      >
        <span style={{ color: "#777", fontSize: 11, fontWeight: 600 }}>
          최근 {items.length}개 연도 기준
        </span>
        <span style={{ color: "#1A237E", fontSize: 14, fontWeight: 800 }}>
          최신 {latest.year}년 {formatScoreValue(latest.value)}
        </span>
      </div>

      <svg
        viewBox={`0 0 ${width} ${height}`}
        role="img"
        aria-label="ESG 종합점수 추이 그래프"
        style={{ display: "block", width: "100%", height: "auto" }}
      >
        {[0, 25, 50, 75, 100].map((tick) => {
          const y = padding.top + plotHeight - (tick / 100) * plotHeight;
          return (
            <g key={tick}>
              <line
                x1={padding.left}
                x2={width - padding.right}
                y1={y}
                y2={y}
                stroke="#E8EAF0"
                strokeWidth="1"
              />
              <text
                x={padding.left - 8}
                y={y + 4}
                textAnchor="end"
                fill="#888"
                fontSize="10"
              >
                {tick}
              </text>
            </g>
          );
        })}

        <polyline
          points={linePoints}
          fill="none"
          stroke="#1A237E"
          strokeWidth="3"
          strokeLinejoin="round"
          strokeLinecap="round"
        />

        {points.map((point) => (
          <g key={point.year}>
            <circle cx={point.x} cy={point.y} r="4.5" fill="#1A237E" />
            <text
              x={point.x}
              y={height - 12}
              textAnchor="middle"
              fill="#666"
              fontSize="11"
              fontWeight="700"
            >
              {point.year}
            </text>
            <text
              x={point.x}
              y={Math.max(12, point.y - 9)}
              textAnchor="middle"
              fill="#333"
              fontSize="10"
              fontWeight="700"
            >
              {point.value.toFixed(1)}
            </text>
          </g>
        ))}
      </svg>
    </div>
  );
}
