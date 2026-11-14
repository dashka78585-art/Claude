// Фирменные вставки (эскизы утверждены Дарьей 13.11.2026, палитра «Тёплый кабинет» 14.11.2026).
// Время в props — по смонтированному ролику (секунды). beats — моменты в речи, к которым привязаны шаги анимации.
import React from "react";
import { AbsoluteFill, Easing, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";

export const C = { bo: "#6B2430", len: "#F2ECE0", car: "#B7957B", rose: "#E5A0B2", choc: "#3E2A24", spark: "#F2D27A" };
const easeOut = Easing.bezier(0.16, 1, 0.3, 1);
const clamp = { extrapolateLeft: "clamp" as const, extrapolateRight: "clamp" as const };

export type Insert = {
  type: "icons" | "strike" | "scheme" | "endcard";
  start: number; end: number; beats: number[];
  items?: string[];          // подписи иконок / слова списка / строки финальной карточки
  icons?: string[];          // ключи иконок: drop | moon | battery | ...
  big?: string; script?: string;   // strike: крупное слово и рукописная строка
  left?: string; right?: string; result?: string; // scheme
  sign?: string;             // endcard: рукописная подпись
};

// локальное время вставки: f — кадр от начала вставки
const useLocal = (ins: Insert) => {
  const f = useCurrentFrame(); const { fps } = useVideoConfig();
  const t = f / fps + ins.start;                       // абсолютное время ролика
  const beat = (i: number) => (ins.beats[i] ?? ins.start) - ins.start; // секунды от начала вставки
  const outP = interpolate(t, [ins.end - 0.25, ins.end], [1, 0], clamp);
  return { f, fps, t, beat, outP };
};

const ICONS: Record<string, React.ReactNode> = {
  drop: <><path d="M32 6C22 20 14 30 14 40a18 18 0 0 0 36 0C50 30 42 20 32 6z" /><path d="M30 24l5 8-6 6 5 8" /></>,
  moon: <><path d="M40 8a24 24 0 1 0 16 38A20 20 0 0 1 40 8z" /><path d="M46 16h6l-6 7h6" /></>,
  battery: <><rect x="8" y="20" width="42" height="24" rx="5" /><path d="M54 28v8" /><path d="M14 26v12" /></>,
};

export const IconsInsert: React.FC<{ ins: Insert }> = ({ ins }) => {
  const { f, fps, beat, outP } = useLocal(ins);
  return (
    <AbsoluteFill style={{ opacity: outP }}>
      <div style={{ position: "absolute", left: 40, right: 40, top: 170, display: "flex", justifyContent: "center", gap: 40 }}>
        {(ins.items ?? []).map((label, i) => {
          const s = spring({ frame: f - beat(i) * fps, fps, config: { damping: 11, stiffness: 200 } });
          const lp = interpolate(f - beat(i) * fps, [3, 12], [0, 1], { ...clamp, easing: easeOut });
          return (
            <div key={i} style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 16, width: 260 }}>
              <div style={{ width: 170, height: 170, borderRadius: "50%", background: C.len, display: "grid", placeItems: "center",
                transform: `scale(${s})`, boxShadow: "0 8px 24px rgba(62,42,36,.18)" }}>
                <svg viewBox="0 0 64 64" style={{ width: 96, height: 96, stroke: C.bo, strokeWidth: 5, fill: "none", strokeLinecap: "round", strokeLinejoin: "round" }}>
                  {ICONS[ins.icons?.[i] ?? "drop"]}
                </svg>
              </div>
              <span style={{ background: "rgba(107,36,48,.9)", color: C.len, padding: "10px 24px 14px", borderRadius: 24, font: "44px Stolzl", whiteSpace: "nowrap",
                opacity: lp, transform: `translateY(${(1 - lp) * -20}px)` }}>{label}</span>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

export const StrikeInsert: React.FC<{ ins: Insert }> = ({ ins }) => {
  const { f, fps, beat, outP } = useLocal(ins);
  const inP = spring({ frame: f, fps, config: { damping: 13, stiffness: 160 } });
  const outline = { paintOrder: "stroke fill" as const, WebkitTextStroke: "14px #fff" };
  return (
    <AbsoluteFill style={{ opacity: outP }}>
      <div style={{ position: "absolute", left: 0, right: 0, top: 1000, textAlign: "center" }}>
        <div style={{ font: "300px/1 StolzlBold", color: C.bo, ...outline, transform: `scale(${0.7 + 0.3 * inP})`, opacity: inP }}>{ins.big}</div>
        <div style={{ font: "110px/1 Sacramento", color: C.bo, ...outline, WebkitTextStroke: "10px #fff", marginTop: -40,
          clipPath: `inset(-40% ${interpolate(f, [4, 18], [100, 0], clamp)}% -40% -10%)` }}>{ins.script}</div>
        <div style={{ display: "inline-flex", gap: 22, marginTop: 30 }}>
          {(ins.items ?? []).map((w, i) => {
            const st = interpolate(f - beat(i) * fps, [0, 8], [0, 100], { ...clamp, easing: easeOut });
            const ap = interpolate(f, [8 + i * 3, 16 + i * 3], [0, 1], clamp);
            return (
              <div key={i} style={{ position: "relative", background: "rgba(107,36,48,.9)", color: C.len, padding: "12px 30px 16px", borderRadius: 26,
                font: "50px Stolzl", opacity: ap, transform: `translateY(${(1 - ap) * 20}px)` }}>
                {w}
                <div style={{ position: "absolute", left: 14, top: "52%", height: 7, width: `calc(${st}% - 28px)`, background: C.spark, borderRadius: 4, transform: "rotate(-4deg)" }} />
              </div>
            );
          })}
        </div>
      </div>
    </AbsoluteFill>
  );
};

export const SchemeInsert: React.FC<{ ins: Insert }> = ({ ins }) => {
  const { f, fps, beat, outP } = useLocal(ins);
  const card = spring({ frame: f, fps, config: { damping: 14, stiffness: 170 } });
  const arrows = interpolate(f, [10, 26], [1, 0], { ...clamp, easing: easeOut });
  const res = spring({ frame: f - beat(1) * fps, fps, config: { damping: 11, stiffness: 190 } });
  const box: React.CSSProperties = { flex: 1, border: `4px solid ${C.bo}`, borderRadius: 30, padding: "22px 14px", font: "44px/1.2 Stolzl", color: C.choc };
  return (
    <AbsoluteFill style={{ opacity: outP }}>
      <div style={{ position: "absolute", left: 60, right: 60, top: 120, background: C.len, borderRadius: 44, padding: "44px 46px 40px", textAlign: "center",
        boxShadow: "0 12px 40px rgba(62,42,36,.22)", transform: `translateY(${(1 - card) * -60}px)`, opacity: card }}>
        <div style={{ display: "flex", gap: 24 }}><div style={box} dangerouslySetInnerHTML={{ __html: ins.left ?? "" }} /><div style={box} dangerouslySetInnerHTML={{ __html: ins.right ?? "" }} /></div>
        <svg viewBox="0 0 900 130" style={{ width: "100%", height: 120, stroke: C.bo, strokeWidth: 5, fill: "none", strokeLinecap: "round" }}>
          <path d="M225 8 C225 80 450 60 450 124" pathLength={1} strokeDasharray={1} strokeDashoffset={arrows} />
          <path d="M675 8 C675 80 450 60 450 124" pathLength={1} strokeDasharray={1} strokeDashoffset={arrows} />
        </svg>
        <div style={{ display: "inline-block", background: C.bo, color: C.len, borderRadius: 30, padding: "20px 46px 24px", font: "54px Stolzl", transform: `scale(${res})` }}>
          {ins.result} <span style={{ color: C.spark }}>✓</span>
        </div>
      </div>
    </AbsoluteFill>
  );
};

export const EndCardInsert: React.FC<{ ins: Insert }> = ({ ins }) => {
  const { f, fps, beat } = useLocal(ins);
  const bg = interpolate(f, [0, 8], [0, 1], { ...clamp, easing: easeOut });
  const items = ins.items ?? [];
  return (
    <AbsoluteFill style={{ background: C.bo, opacity: bg, display: "flex", flexDirection: "column", justifyContent: "center", padding: "0 110px" }}>
      {items.map((line, i) => {
        const p = interpolate(f - beat(i) * fps, [0, 10], [0, 1], { ...clamp, easing: easeOut });
        return <div key={i} style={{ font: "100px/1.2 Stolzl", whiteSpace: "nowrap", color: i === items.length - 1 ? C.spark : C.len, opacity: p,
          transform: `translateY(${(1 - p) * 40}px)` }}>{line}</div>;
      })}
      {ins.sign ? (
        <div style={{ font: "190px/1 Sacramento", color: C.rose, marginTop: 40, alignSelf: "flex-end", transform: "rotate(-4deg)",
          clipPath: `inset(-40% ${interpolate(f - beat(items.length) * fps, [0, 9], [100, 0], clamp)}% -40% -10%)` }}>{ins.sign}</div>
      ) : null}
    </AbsoluteFill>
  );
};

export const InsertLayer: React.FC<{ ins: Insert }> = ({ ins }) => {
  if (ins.type === "icons") return <IconsInsert ins={ins} />;
  if (ins.type === "strike") return <StrikeInsert ins={ins} />;
  if (ins.type === "scheme") return <SchemeInsert ins={ins} />;
  return <EndCardInsert ins={ins} />;
};
