import React from "react";
import { AbsoluteFill, Sequence, interpolate, spring, useCurrentFrame, useVideoConfig, Easing } from "remotion";

export type Chunk = [number, number, string]; // [start s, end s, html] — время уже по смонтированному ролику
export type Headline = { main: string; accent?: string; tail?: string; color?: "bordeaux" | "green"; until: number };
export type OverlayProps = { headline: Headline; chunks: Chunk[]; durationInFrames: number };

const ACC = { bordeaux: "#6E1F2F", green: "#3E4A2C" };
const shadow = "0 3px 24px rgba(0,0,0,.22)";
const easeOut = Easing.bezier(0.16, 1, 0.3, 1);

const HeadlineLayer: React.FC<{ h: Headline }> = ({ h }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const out = h.until * fps;
  const exit = interpolate(f, [out, out + 0.3 * fps], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const lines = h.main.split(/<br\s*\/?>/i);
  const accIn = interpolate(f, [8, 22], [100, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: easeOut });
  const tailS = spring({ frame: f - 16, fps, config: { damping: 12, stiffness: 180 } });
  return (
    <AbsoluteFill style={{ opacity: exit, transform: `translateY(${(1 - exit) * -30}px)` }}>
      <div style={{ position: "absolute", left: 0, right: 0, top: 150, textAlign: "center" }}>
        {lines.map((l, i) => {
          const p = interpolate(f, [i * 4, i * 4 + 12], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: easeOut });
          return (
            <div key={i} style={{ whiteSpace: "nowrap", font: "228px/0.86 Oswald", textTransform: "uppercase", color: "#fff",
              textShadow: shadow, opacity: p, transform: `translateY(${(1 - p) * 60}px) scale(${1.06 - 0.06 * p})` }}
              dangerouslySetInnerHTML={{ __html: l }} />
          );
        })}
        {h.accent ? (
          <div style={{ position: "relative", display: "inline-block", transform: "rotate(-7deg)", marginTop: -250, left: -40,
            font: "200px/1 Sacramento", color: ACC[h.color ?? "bordeaux"], paintOrder: "stroke fill", WebkitTextStroke: "14px #fff",
            clipPath: `inset(-40% ${accIn}% -40% -10%)` }}>{h.accent}</div>
        ) : null}
        {h.tail ? (
          <div style={{ font: "96px/1 StolzlBold", color: "#fff", textAlign: "right", paddingRight: 70, marginTop: 40, textShadow: shadow,
            transform: `scale(${tailS})`, transformOrigin: "right center" }}>{h.tail}</div>
        ) : null}
      </div>
    </AbsoluteFill>
  );
};

const SubtitleLayer: React.FC<{ html: string }> = ({ html }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame: f, fps, config: { damping: 14, stiffness: 220, mass: 0.6 } });
  return (
    <div style={{ position: "absolute", top: 1400, left: 0, right: 0, textAlign: "center", whiteSpace: "nowrap" }}>
      <span className="sub" style={{ display: "inline-block", background: "rgba(110,106,78,.85)", padding: "14px 34px 18px", borderRadius: 30,
        font: "66px/1.15 Stolzl", color: "#fff", opacity: Math.min(1, s * 1.4), transform: `translateY(${(1 - s) * 26}px) scale(${0.86 + 0.14 * s})` }}
        dangerouslySetInnerHTML={{ __html: html }} />
    </div>
  );
};

export const Overlay: React.FC<OverlayProps> = ({ headline, chunks }) => {
  const { fps } = useVideoConfig();
  return (
    <AbsoluteFill style={{ backgroundColor: "transparent" }}>
      <style>{`.sub b{font:96px/0.6 PeachCream;font-weight:normal;padding:0 4px;position:relative;top:6px}.sub i{font-style:normal;color:#F5DE9A}`}</style>
      {chunks.map(([s, e, html], i) => (
        <Sequence key={i} from={Math.round(s * fps)} durationInFrames={Math.max(1, Math.round((e - s) * fps))} layout="none">
          <SubtitleLayer html={html} />
        </Sequence>
      ))}
      <Sequence durationInFrames={Math.round((headline.until + 0.4) * fps)} layout="none">
        <HeadlineLayer h={headline} />
      </Sequence>
    </AbsoluteFill>
  );
};
