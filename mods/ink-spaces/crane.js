import { div, image } from "gpui-kit";

// Selection observation is pure state bookkeeping. Playback begins only in the
// first-layout event, never by scheduling work or notifying during render.
export class CraneMotion {
  constructor(namespace = "row") {
    this.namespace = namespace;
    this.key = undefined;
    this.generation = 0;
    this.phase = "rest";
    this.pending = null;
  }

  observe(key) {
    key = key ?? null;
    if (key === this.key) return;
    const first = this.key === undefined;
    this.key = key;
    this.generation += 1;
    this.phase = first || !key ? "rest" : "armed";
  }

  start(key, generation, cx) {
    if (key !== this.key || generation !== this.generation || this.phase !== "armed") return;
    this.pending?.cancel();
    this.phase = "playing";
    // One phase deadline only. All wing frames play natively in the GIF;
    // position and opacity use native transitions, with no per-frame JS timer.
    this.pending = cx.timer.after(2000, (next) => {
      if (key !== this.key || generation !== this.generation) return;
      this.pending = null;
      this.phase = "rest";
      next.notify();
    });
    cx.notify();
  }

  render(key) {
    if (!key || key !== this.key) return div().absolute().w(0).h(0);
    const generation = this.generation;
    const armed = this.phase === "armed";
    const animated = this.phase !== "rest";
    return div().id(`crane-slot-${this.namespace}-${key}-${generation}`).absolute().right(4).top(1).w(36).h(34).overflow_hidden()
      .on_size_change((_size, cx) => this.start(key, generation, cx))
      .child(image(animated ? "mods/ink-chrome/art/crane-arrival-ink-left-v8.gif" : "mods/ink-chrome/art/crane-rest-ink-left-v8.png")
        .id(`crane-${this.namespace}-${key}-${generation}`).absolute().w(34).h(33)
        .left(armed ? 14 : 0).top(armed ? -5 : 0).opacity(armed ? 0 : 0.88)
        .transition("left", { duration: 1600, easing: "ease-out" })
        .transition("top", { duration: 1600, easing: "ease-out" })
        .transition("opacity", { duration: 400, easing: "ease-out" }));
  }

  cancel() {
    this.generation += 1;
    this.pending?.cancel();
    this.pending = null;
    this.phase = "rest";
  }
}
