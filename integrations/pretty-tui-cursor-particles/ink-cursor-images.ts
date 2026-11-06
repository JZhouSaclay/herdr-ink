import { readFileSync } from "node:fs";
import { allocateImageId } from "@earendil-works/pi-tui";

const ESC = "\x1b";
const kitty = (controls: string, data = "") => `${ESC}_G${controls};${data}${ESC}\\`;
const ART = new Map<string, string>();
for (const key of ["ink", ...Array.from({ length: 24 }, (_, i) => `leaf-${String(i).padStart(2, "0")}`)]) {
  ART.set(key, readFileSync(new URL(`./art/cursor-${key}.png`, import.meta.url)).toString("base64"));
}
export type CursorPosition = { row: number; col: number };
/** Read Pi's final, visible cursor, after layout, overlays and clipping. */
export function nativeFrameCursor(data: string): CursorPosition | undefined {
  const match = /\x1b\[(\d+);(\d+)H\x1b\[\?25h\x1b\[\?2026l$/.exec(data);
  return match ? { row: Number(match[1]), col: Number(match[2]) } : undefined;
}

/** Transparent cursor overlay, up to one Chinese glyph wide. */
export class InkCursorImagePainter {
  private cache = new Map<string, { id: number; uploaded: boolean }>();
  private placed?: number;
  private style?: string;
  private started = 0;
  private columns = Number.POSITIVE_INFINITY;
  position?: CursorPosition;
  constructor(private now: () => number = Date.now) {}
  get visible() { return this.placed !== undefined; }
  get animated() { return this.style === "leaf" && !!this.position; }
  paint(position: CursorPosition | undefined, style: unknown, reset = false, columns = Number.POSITIVE_INFINITY): string {
    this.columns = columns;
    let out = "";
    if (reset) {
      for (const entry of this.cache.values()) entry.uploaded = false;
      this.placed = undefined;
    } else if (this.placed !== undefined) out += kitty(`a=d,d=i,i=${this.placed},q=2`);
    this.placed = undefined;
    if (!position || !["leaf", "leaf-still", "ink"].includes(String(style))) {
      this.position = undefined;this.style = undefined;return out;
    }
    if (position.row !== this.position?.row || position.col !== this.position?.col || style !== this.style) this.started = this.now();
    this.position = { ...position };this.style = String(style);
    const frame = this.animated ? Math.floor((this.now() - this.started) / 100) % 24 : 0;
    const key = style === "ink" ? "ink" : `leaf-${String(frame).padStart(2,"0")}`;
    let entry = this.cache.get(key);
    if (!entry) { entry = { id: allocateImageId(), uploaded: false };this.cache.set(key, entry); }
    if (!entry.uploaded) {
      const data = ART.get(key)!;
      for (let offset = 0; offset < data.length; offset += 4096) {
        const more = offset + 4096 < data.length ? 1 : 0;
        out += kitty(offset === 0 ? `a=t,f=100,i=${entry.id},q=2,m=${more}` : `m=${more}`, data.slice(offset, offset + 4096));
      }
      entry.uploaded = true;
    }
    this.placed = entry.id;
    const width = style === "ink" ? 1 : Math.max(1, Math.min(2, columns - position.col + 1));
    return out + `${ESC}[${position.row};${position.col}H` + kitty(`a=p,i=${entry.id},p=1,c=${width},r=1,z=2,C=1,q=2`);
  }
  tick() { return this.paint(this.position, this.style, false, this.columns); }
  dispose() {
    const out = [...this.cache.values()].map(entry => kitty(`a=d,d=I,i=${entry.id},q=2`)).join("");
    this.cache.clear();this.position = undefined;this.placed = undefined;this.style = undefined;return out;
  }
}
