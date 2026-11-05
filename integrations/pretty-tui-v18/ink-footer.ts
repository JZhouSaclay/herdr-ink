import { readFileSync } from "node:fs";
import { allocateImageId, visibleWidth } from "@earendil-works/pi-tui";

const ESC = "\x1b";
const MARKER = /\x1b\]1337;InkFooter=(model|scroll|wind)\x07/g;
const SYMBOLS: Record<string, string> = { "✦": "model", "🧠": "scroll", "⚡": "wind" };
const WIDTHS: Record<string, number> = { model: 1, scroll: 2, wind: 2 };
const ART = new Map<string, string>();
// Load once per extension runtime; no disk reads during terminal rendering.
for (const kind of Object.values(SYMBOLS)) {
  ART.set(kind, readFileSync(new URL(`./art/footer-${kind}-v18.png`, import.meta.url)).toString("base64"));
}
export const stripFooterMarkers = (line: string) => line.replace(MARKER, "");
export function inkFooterLine(line: string): string {
  // Restrict this transform to footer-container output, preserving ANSI styles,
  // visible columns and every status value. The native glyph remains the fallback.
  return line.replace(/✦|🧠|⚡\uFE0F?/gu, (symbol) => {
    const kind = SYMBOLS[symbol.replace("\uFE0F", "")];
    return `${ESC}]1337;InkFooter=${kind}\x07${" ".repeat(visibleWidth(symbol))}`;
  });
}
const kitty = (controls: string, payload = "") => `${ESC}_G${controls};${payload}${ESC}\\`;
export class FooterImagePainter {
  private cache = new Map<string, { id: number; uploaded: boolean }>();
  paint(lines: string[], columns: number, reset: boolean, hidden: boolean): string {
    let output = "";
    for (const icon of this.cache.values()) {
      if (reset) icon.uploaded = false;
      else output += kitty(`a=d,d=i,i=${icon.id},q=2`);
    }
    const used = new Set<string>();
    let placement = 1;
    for (let y = 0; !hidden && y < lines.length; y++) {
      for (const match of lines[y].matchAll(MARKER)) {
        const kind = match[1];
        const x = visibleWidth(lines[y].slice(0, match.index));
        const width = WIDTHS[kind];
        // Don't draw an icon if its reserved cells were truncated by the TUI.
        if (x < 0 || x + width > columns || visibleWidth(lines[y]) < x + width) continue;
        let icon = this.cache.get(kind);
        if (!icon) { icon = { id: allocateImageId(), uploaded: false }; this.cache.set(kind, icon); }
        used.add(kind);
        if (!icon.uploaded) {
          const data = ART.get(kind)!;
          for (let offset = 0; offset < data.length; offset += 4096) {
            const more = offset + 4096 < data.length ? 1 : 0;
            output += kitty(offset === 0 ? `a=t,f=100,i=${icon.id},q=2,m=${more}` : `m=${more}`, data.slice(offset, offset + 4096));
          }
          icon.uploaded = true;
        }
        output += `${ESC}[${y+1};${x+1}H` + kitty(`a=p,i=${icon.id},p=${placement++},c=${width},r=1,z=1,C=1,q=2`);
      }
    }
    for (const [kind,icon] of this.cache) {
      if (used.has(kind)) continue;
      output += kitty(`a=d,d=I,i=${icon.id},q=2`);this.cache.delete(kind);
    }
    return output ? `${ESC}7${output}${ESC}8` : "";
  }
  dispose(): string {
    const output = [...this.cache.values()].map(icon => kitty(`a=d,d=I,i=${icon.id},q=2`)).join("");
    this.cache.clear();return output;
  }
}

const PATCH = Symbol.for("pretty-tui.ink-footer");
export function createInkFooter(getEnabled: () => boolean) {
  const cleanups = new Map<any, () => void>();
  return {
    attach(container: any) {
      if (!container || typeof container.render !== "function" || container[PATCH]) return;
      const descriptor = Object.getOwnPropertyDescriptor(container, "render");
      const original = container.render;
      const render = function(this: any, width: number): string[] {
        const lines = original.call(this, width);
        return getEnabled() ? lines.map(inkFooterLine) : lines;
      };
      container[PATCH] = true;container.render = render;container.invalidate?.();
      cleanups.set(container, () => {
        if (container.render === render) {
          if (descriptor) Object.defineProperty(container,"render",descriptor);
          else delete container.render;
        }
        delete container[PATCH];container.invalidate?.();
      });
    },
    dispose() { for (const cleanup of cleanups.values()) cleanup();cleanups.clear(); },
  };
}
