import React from "react";
import { Composition, continueRender, delayRender } from "remotion";
import { Overlay, OverlayProps } from "./Overlay";
import { fontsReady } from "./fonts";

const handle = delayRender("fonts");
fontsReady.then(() => continueRender(handle)).catch((e) => { console.error(e); continueRender(handle); });

const defaults: OverlayProps = {
  headline: { main: "Мне муж<br>не даст", accent: "бросить", tail: "ГВ", color: "bordeaux", until: 2.3 },
  chunks: [[0, 1.2, "«Муж мне не даст"], [1.2, 2.5, "бросить ГВ»"], [2.5, 3.2, "<b>ужасная</b>"]],
  durationInFrames: 120,
};

export const RemotionRoot: React.FC = () => (
  <Composition id="Overlay" component={Overlay} fps={30} width={1080} height={1920}
    durationInFrames={defaults.durationInFrames} defaultProps={defaults}
    calculateMetadata={({ props }) => ({ durationInFrames: props.durationInFrames })} />
);
