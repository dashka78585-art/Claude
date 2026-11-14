import { loadFont } from "@remotion/fonts";
import { staticFile } from "remotion";

// Шрифты кладёт в public/fonts скрипт render_overlay.sh (бесплатные из fonts/ скилла + платные от Дарьи).
const FONTS: [string, string][] = [
  ["Oswald", "Oswald-Bold.ttf"],
  ["Sacramento", "Sacramento.ttf"],
  ["Stolzl", "stolzl_regular.otf"],
  ["StolzlBold", "stolzl_bold.otf"],
  ["PeachCream", "Peach_Cream.otf"],
];
export const fontsReady = Promise.all(
  FONTS.map(([family, file]) => loadFont({ family, url: staticFile(`fonts/${file}`) })),
);
