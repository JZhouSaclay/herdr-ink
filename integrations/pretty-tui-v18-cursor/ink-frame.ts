/** Deterministic dry-brush coverage in absolute image coordinates. */
export const INK_FRAME_FLAG = 0x1000000;
export type FrameCell = { widthPx: number; heightPx: number; topGap?: number };
export function inkFrameAlpha(x: number, y: number, width: number, height: number, cell: FrameCell): number {
  const left = cell.widthPx / 2, right = width - left;
  const top = cell.heightPx / 2, bottom = height - top;
  const stroke = Math.max(1.1, cell.heightPx * .065);
  let distance = Infinity;
  if (y >= top - stroke && y <= bottom + stroke) {
    const drift = .65 * Math.sin(y / 17) + .25 * Math.sin(y / 4.7);
    distance = Math.min(Math.abs(x-left-drift), Math.abs(x-right+drift));
  }
  if (x >= left - stroke && x <= right + stroke) {
    const drift = .55 * Math.sin(x / 27) + .3 * Math.sin(x / 7.3);
    // Leave the native working indicator and elapsed time unobstructed.
    if (!(cell.topGap && x > cell.widthPx && x < cell.topGap * cell.widthPx)) distance = Math.min(distance,Math.abs(y-top-drift));
    distance = Math.min(distance,Math.abs(y-bottom+drift));
  }
  const wash = .52 + .12*Math.sin(x*.29+y*.19) + .07*Math.sin(x*1.1-y*.71);
  return Math.round(255*Math.max(0,1-distance/stroke)*wash);
}
