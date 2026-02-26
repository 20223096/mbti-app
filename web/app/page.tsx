"use client";

import { useMemo, useState, useEffect } from "react";

type ChatMsg = { role: "user" | "assistant"; content: string; followUps?: string[]; };

type TraitsProfile = {
  type: string;
  base: any;
  state: any;
  evidence: any[];
};

type ChatResponse = {
  assistant_message?: string;
  analysis_json?: {
    updated_traits_patch?: { path: string; value: any }[];
    follow_up_questions?: string[];
    confidence?: number;
    summary?: string;
    mbti_hypothesis?: any;
    interpretation?: any;
    reasons_top3?: any;
    actions?: any;
    message_examples?: any;
    reality_check?: string;
    comfort?: string;
    disclaimer?: string;
  };
};

function applyPatchToState(original: TraitsProfile, patch: { path: string; value: any }[]) {
  const updated: TraitsProfile = JSON.parse(JSON.stringify(original));

  patch.forEach(({ path, value }) => {
    const keys = path.split(".");
    let target = updated.state;

    for (let i = 0; i < keys.length - 1; i++) {
      if (!target[keys[i]]) target[keys[i]] = {};
      target = target[keys[i]];
    }
    target[keys[keys.length - 1]] = value;
  });

  return updated;
}

export default function Home() {
  const [mbti, setMbti] = useState("");
  const [relationshipType, setRelationshipType] = useState("");
  const [relationshipState, setRelationshipState] = useState("");

  const [traitsProfile, setTraitsProfile] = useState<TraitsProfile | null>(null);

  const [messages, setMessages] = useState<ChatMsg[]>([
    {
      role: "assistant",
      content: "안녕! 상황을 말해줘 🙂",
    },
  ]);

  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);

  const base = useMemo(
    () => process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000",
    []
  );

  // ✅ MBTI 바뀌면 traits_profile 로컬스토리지와 state를 맞춤
  useEffect(() => {
    if (!mbti) return;

    const stored = localStorage.getItem("traits_profile");

    if (stored) {
      const parsed = JSON.parse(stored);
      if (parsed?.type === mbti) {
        setTraitsProfile(parsed);
        return;
      }
    }

    const initial: TraitsProfile = {
      type: mbti,
      base: {},
      state: {
        context: {
          memory: {
            timeline: [],
            patterns: [],
          },
        },
      },
      evidence: [],
    };

    localStorage.setItem("traits_profile", JSON.stringify(initial));
    setTraitsProfile(initial);
  }, [mbti]);

  const send = async () => {
    const text = input.trim();
    if (!text || sending) return;

    const latestTraitsProfile : TraitsProfile | null = (() => {
      const stored = localStorage.getItem("traits_profile");
      if (stored) {
        try { return JSON.parse(stored); } catch {}
      }
      return traitsProfile;
    })();

    // 1) 유저 메시지 즉시 반영
    const nextMessages: ChatMsg[] = [...messages, { role: "user", content: text }];
    setMessages(nextMessages);
    setInput("");
    setSending(true);

    try {
      const res = await fetch(`${base}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          messages: nextMessages,
          mbti: mbti || null,
          relationship_type: relationshipType || null,
          relationship_state: relationshipState || null,
          traits_profile: latestTraitsProfile || null,
        }),
      });

      if (!res.ok) throw new Error(`API Error: ${res.status}`);

      const data: ChatResponse = await res.json();

      // 2) ✅ 서버가 준 patch는 "data.analysis_json.updated_traits_patch" 안에 있음
      const patch = data?.analysis_json?.updated_traits_patch;

      if (Array.isArray(patch) && latestTraitsProfile) {
        const updated = applyPatchToState(latestTraitsProfile, patch);
        localStorage.setItem("traits_profile", JSON.stringify(updated));
        setTraitsProfile(updated);

        // 디버그로 확인하고 싶으면 켜
        // console.log("LLM patch applied:", patch);
      }
      const followUps = data?.analysis_json?.follow_up_questions ?? [];

      // 3) 봇 메시지 추가
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: data.assistant_message ?? "응답이 비었어.",
          followUps : Array.isArray(followUps) ? followUps.slice(0, 3) : [],
        },
      ]);
    } catch (e: any) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: `에러: ${e?.message || "Unknown error"}` },
      ]);
    } finally {
      setSending(false);
    }
  };

  const onKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  const resetAll = () => {
    setMessages([{ role: "assistant", content: "대화를 초기화했어. 다시 말해줘!" }]);
    localStorage.removeItem("traits_profile");
    setTraitsProfile(null);
  };

  return (
    <main style={{ maxWidth: 820, margin: "40px auto", padding: 16 }}>
      <div style={{ display: "flex", justifyContent: "space-between", gap: 12 }}>
        <div>
          <h1 style={{ fontSize: 28, fontWeight: 800 }}>AI 관계 해석 챗봇</h1>
          <p style={{ marginTop: 6, opacity: 0.75 }}>
            API BASE: <code>{base}</code>
          </p>
        </div>
      </div>

      {/* 옵션 */}
      <section
        style={{
          marginTop: 16,
          padding: 12,
          border: "1px solid #ddd",
          borderRadius: 8,
          display: "grid",
          gap: 10,
        }}
      >
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
          <input
            placeholder="MBTI (예: ISTP)"
            value={mbti}
            onChange={(e) => setMbti(e.target.value.toUpperCase())}
            style={{ padding: 12, border: "1px solid #ccc", borderRadius: 8 }}
          />
          <input
            placeholder="relationship_type (예: romantic_interest)"
            value={relationshipType}
            onChange={(e) => setRelationshipType(e.target.value)}
            style={{ padding: 12, border: "1px solid #ccc", borderRadius: 8 }}
          />
        </div>

        <input
          placeholder="relationship_state (예: exploring)"
          value={relationshipState}
          onChange={(e) => setRelationshipState(e.target.value)}
          style={{ padding: 12, border: "1px solid #ccc", borderRadius: 8 }}
        />

        {/* (선택) 지금 traits state 확인용 */}
        <details style={{ marginTop: 4 }}>
          <summary style={{ cursor: "pointer" }}>traits_profile 보기(디버그)</summary>
          <pre style={{ fontSize: 12, overflowX: "auto" }}>
            {JSON.stringify(traitsProfile, null, 2)}
          </pre>
        </details>
      </section>

      {/* 채팅 */}
      <section
        style={{
          marginTop: 16,
          border: "1px solid #ddd",
          borderRadius: 8,
          padding: 12,
          height: 520,
          overflowY: "auto",
          display: "flex",
          flexDirection: "column",
          gap: 10,
          background: "#fafafa",
        }}
      >
        {messages.map((m, idx) => {
          const isUser = m.role === "user";
          return (
            <div
              key={idx}
              style={{ display: "flex", justifyContent: isUser ? "flex-end" : "flex-start" }}
            >
              <div
                style={{
                  maxWidth: "78%",
                  padding: "10px 12px",
                  borderRadius: 12,
                  border: "1px solid #e5e5e5",
                  background: isUser ? "#dbeafe" : "#fff",
                  whiteSpace: "pre-wrap",
                  lineHeight: 1.5,
                }}
              >
                {m.content}

                {m.role === "assistant" && m.followUps && m.followUps.length > 0 && (
  <div style={{ marginTop: 8, display: "flex", flexWrap: "wrap", gap: 8 }}>
    {m.followUps.map((q, i) => (
      <button
        key={i}
        type="button"
        onClick={() => {
          setInput((prev) => (prev ? `${prev}\n${q}` : q)); // ✅ 클릭하면 입력창에 추가
        }}
        style={{
          padding: "6px 10px",
          borderRadius: 999,
          border: "1px solid #cbd5e1",
          background: "#f1f5f9",
          cursor: "pointer",
          fontSize: 12,
        }}
      >
        {q}
      </button>
    ))}
  </div>
)}
              </div>
            </div>
          );
        })}

        {sending && (
          <div style={{ display: "flex", justifyContent: "flex-start" }}>
            <div
              style={{
                padding: "10px 12px",
                borderRadius: 12,
                border: "1px solid #e5e5e5",
                background: "#fff",
                opacity: 0.8,
              }}
            >
              입력 중…
            </div>
          </div>
        )}
      </section>

      {/* 입력 */}
      <section style={{ marginTop: 12, display: "grid", gap: 10 }}>
        <textarea
          placeholder="상황을 입력하고 Enter로 전송 (Shift+Enter 줄바꿈)"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={onKeyDown}
          rows={3}
          style={{
            width: "100%",
            padding: 12,
            borderRadius: 8,
            border: "1px solid #ccc",
          }}
        />

        <div style={{ display: "flex", gap: 10, justifyContent: "flex-end" }}>
          <button
            onClick={resetAll}
            disabled={sending}
            style={{ padding: "10px 12px", borderRadius: 8, border: "1px solid #ccc" }}
          >
            초기화
          </button>

          <button
            onClick={send}
            disabled={!input.trim() || sending}
            style={{
              padding: "10px 14px",
              borderRadius: 8,
              border: "1px solid #0f172a",
              fontWeight: 800,
            }}
          >
            {sending ? "전송 중..." : "전송"}
          </button>
        </div>
      </section>
    </main>
  );
}