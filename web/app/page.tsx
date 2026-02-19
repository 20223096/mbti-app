"use client";

import { useState } from "react";

type Likelihood = "high" | "medium" | "low";

type Result = {
  summary: string;
  interpretation: { mbti_view: string; why_this_matters: string };
  reasons_top3: Array<{
    reason: string;
    likelihood: Likelihood;
    signals_to_check: string[];
    risk_of_misread: string;
  }>;
  actions: { do: string[]; avoid: string[] };
  message_examples: Array<{ tone: string; text: string }>;
  reality_check: string;
  comfort: string;
  disclaimer: string;
};

export default function Home() {
  const [situation, setSituation] = useState("");
  const [mbti, setMbti] = useState("");
  const [relationshipType, setRelationshipType] = useState("");
  const [relationshipState, setRelationshipState] = useState("");

  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">(
    "idle"
  );
  const [result, setResult] = useState<Result | null>(null);
  const [errorMsg, setErrorMsg] = useState<string>("");
  const base = process.env.NEXT_PUBLIC_API_BASE;
  console.log("API BASE:", process.env.NEXT_PUBLIC_API_BASE);

  const onSubmit = async () => {
    setStatus("loading");
    setErrorMsg("");
    setResult(null);
    

    try {
      const res = await fetch(`${base}/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          situation,
          mbti: mbti || null,
          relationship_type: relationshipType || null,
          relationship_state: relationshipState || null,
        }),
      });

      if (!res.ok) throw new Error(`API Error: ${res.status}`);

      const data: Result = await res.json();

      // ✅ 프론트 방어: 배열 길이 강제
      // 배열 길이 제한 + 기본값
      data.reasons_top3 = Array.isArray(data.reasons_top3) ? data.reasons_top3.slice(0, 3) : [];
      data.message_examples = Array.isArray(data.message_examples) ? data.message_examples.slice(0, 2) : [];
      data.actions = data.actions ?? { do: [], avoid: [] };
      data.interpretation = data.interpretation ?? { mbti_view: "", why_this_matters: "" };
      data.reality_check = data.reality_check ?? "";
      data.comfort = data.comfort ?? "";
      data.disclaimer = data.disclaimer ?? "";
      data.summary = data.summary ?? "";
      setResult(data);
      setStatus("success");
    } catch (e: any) {
      setStatus("error");
      setErrorMsg(e?.message || "Unknown error");
    }
  };

  return (
    <main style={{ maxWidth: 820, margin: "40px auto", padding: 16 }}>
      <h1 style={{ fontSize: 28, fontWeight: 700 }}>AI 관계 해석 MVP</h1>

      {/* 입력 폼 (idle/loading에서도 보이게) */}
      <div style={{ marginTop: 20, display: "grid", gap: 12 }}>
        <textarea
          placeholder="상황을 입력하세요"
          value={situation}
          onChange={(e) => setSituation(e.target.value)}
          rows={5}
          style={{ width: "100%", padding: 12 }}
        />

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
          <input
            placeholder="MBTI (예: ISTP)"
            value={mbti}
            onChange={(e) => setMbti(e.target.value)}
            style={{ padding: 12 }}
          />
          <input
            placeholder="relationship_type (예: romantic_interest)"
            value={relationshipType}
            onChange={(e) => setRelationshipType(e.target.value)}
            style={{ padding: 12 }}
          />
        </div>

        <input
          placeholder="relationship_state (예: exploring)"
          value={relationshipState}
          onChange={(e) => setRelationshipState(e.target.value)}
          style={{ padding: 12 }}
        />

        <button
          onClick={onSubmit}
          disabled={!situation || status === "loading"}
          style={{ padding: 12, fontWeight: 700 }}
        >
          {status === "loading" ? "분석 중..." : "분석하기"}
        </button>
      </div>

      {/* 상태 UI */}
      {status === "idle" && (
        <p style={{ marginTop: 16, opacity: 0.7 }}>
          상황을 입력하고 “분석하기”를 눌러봐.
        </p>
      )}

      {status === "error" && (
        <div style={{ marginTop: 20, padding: 12, border: "1px solid #ccc" }}>
          <b>에러 발생</b>
          <p style={{ marginTop: 8 }}>{errorMsg}</p>
          <button onClick={onSubmit} style={{ marginTop: 10, padding: 10 }}>
            다시 시도
          </button>
        </div>
      )}


      {status === "success" && result && (
        <div style={{ marginTop: 24, display: "grid", gap: 16 }}>
          <section style={{ padding: 12, border: "1px solid #ddd" }}>
            <h2 style={{ fontSize: 18, fontWeight: 700 }}>요약</h2>
            <p style={{ marginTop: 8 }}>{result.summary}</p>
          </section>

          <section style={{ padding: 12, border: "1px solid #ddd" }}>
            <h2 style={{ fontSize: 18, fontWeight: 700 }}>해석</h2>
            <p style={{ marginTop: 8 }}>{result.interpretation?.mbti_view}</p>
            <p style={{ marginTop: 8, opacity: 0.85 }}>
              {result.interpretation?.why_this_matters}
            </p>
          </section>

          <section style={{ padding: 12, border: "1px solid #ddd" }}>
            <h2 style={{ fontSize: 18, fontWeight: 700 }}>가능한 이유 Top3</h2>
            <div style={{ marginTop: 12, display: "grid", gap: 12 }}>
              {result.reasons_top3?.map((r, idx) => (
                <div key={idx} style={{ padding: 12, border: "1px solid #eee" }}>
                  <b>
                    {idx + 1}. {r.reason} ({r.likelihood})
                  </b>
                  <ul style={{ marginTop: 8 }}>
                    {(r.signals_to_check || []).map((s, i) => (
                      <li key={i}>{s}</li>
                    ))}
                  </ul>
                  <p style={{ marginTop: 8, opacity: 0.8 }}>
                    오해 포인트: {r.risk_of_misread}
                  </p>
                </div>
              ))}
            </div>
          </section>

          <section style={{ padding: 12, border: "1px solid #ddd" }}>
            <h2 style={{ fontSize: 18, fontWeight: 700 }}>행동</h2>
            <div style={{ marginTop: 10 }}>
              <b>해볼 것</b>
              <ul>
                {(result.actions?.do || []).map((d, i) => (
                  <li key={i}>{d}</li>
                ))}
              </ul>
            </div>
            <div style={{ marginTop: 10 }}>
              <b>피할 것</b>
              <ul>
                {(result.actions?.avoid || []).map((a, i) => (
                  <li key={i}>{a}</li>
                ))}
              </ul>
            </div>
          </section>

          <section style={{ padding: 12, border: "1px solid #ddd" }}>
            <h2 style={{ fontSize: 18, fontWeight: 700 }}>메시지 예시 (2개)</h2>
            <div style={{ marginTop: 10, display: "grid", gap: 10 }}>
              {result.message_examples?.map((m, i) => (
                <div key={i} style={{ padding: 12, border: "1px solid #eee" }}>
                  <b>{m.tone}</b>
                  <p style={{ marginTop: 6 }}>{m.text}</p>
                </div>
              ))}
            </div>
          </section>

          {/* 하단 3종 */}
          {result.reality_check && (
            <p style={{ marginTop: 4 }}>
              <b>Reality check:</b> {result.reality_check}
            </p>
          )}
          {result.comfort && (
            <p style={{ marginTop: 4 }}>
              <b>Comfort:</b> {result.comfort}
            </p>
          )}
          {result.disclaimer && (
            <p style={{ marginTop: 4, opacity: 0.75 }}>
              <b>Disclaimer:</b> {result.disclaimer}
            </p>
          )}
        </div>
      )}
    </main>
  );
}
