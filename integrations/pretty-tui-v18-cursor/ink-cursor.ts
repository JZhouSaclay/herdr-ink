const STYLES: Record<string, number> = { bar: 6, underline: 4, block: 2 };
const RESET = "\x1b[0 q\x1b]112\x07";
const INK = "\x1b]12;#58695b\x07";
type CursorTui = {
  terminal?: { write(data: string): void };
  getShowHardwareCursor(): boolean;
  setShowHardwareCursor(enabled: boolean): void;
};

/** Preserve the native text/IME position; replace only Pi's inverse-video cursor. */
export function createInkCursor(getStyle: () => unknown) {
  const states = new Map<CursorTui, { previous: boolean; style: number }>();
  function restore(tui: CursorTui) {
    const state = states.get(tui);
    if (!state) return;
    tui.terminal?.write(RESET);
    tui.setShowHardwareCursor(state.previous);
    states.delete(tui);
  }
  return {
    attach(tui: CursorTui | undefined) {
      if (!tui?.terminal?.write || typeof tui.getShowHardwareCursor !== "function" ||
          typeof tui.setShowHardwareCursor !== "function") return;
      const configured = getStyle();
      const style = typeof configured === "string" ? STYLES[configured] : undefined;
      if (style === undefined) { restore(tui); return; }
      const state = states.get(tui);
      // Pi reapplies showHardwareCursor=false during /reload after extensions
      // have attached. A cached shape does not mean the fake cursor is disabled.
      if (state?.style === style && tui.getShowHardwareCursor()) return;
      // Send shape/color before enabling the terminal cursor; no transient block.
      tui.terminal.write(`\x1b[${style} q${INK}`);
      if (!state) states.set(tui, { previous: tui.getShowHardwareCursor(), style });
      else state.style = style;
      tui.setShowHardwareCursor(true);
    },
    dispose() { for (const tui of [...states.keys()]) restore(tui); },
  };
}
