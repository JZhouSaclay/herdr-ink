import { inkLine, inkStamp } from "./ink.js";
import { View, div, svg, image } from "gpui-kit";
import { h_flex } from "gpui-base";
import { spaces, panes, run, openOverlay, theme, window, shared, layout, settings } from "herdr";

function find(node, id) {
  if (node?.id === id) return node;
  for (const child of node?.children ?? []) {
    const found = find(child, id);
    if (found) return found;
  }
  return null;
}

export default class Tabs extends View {
  init() {
    this.hovered = null;
    this.pressed = null;
    this.panels = JSON.parse(localStorage.getItem("panels") ?? "{}");
  }

  // The side panel is remembered per space: switching shows that space's choice
  // (closed if it never had one), and opening or closing it records it.
  syncPanel(space, panel, body, enabled) {
    if (!space || !panel) return;
    const now = panel.hidden ? null : body?.active ?? null;
    if (space.id !== this.space) {
      const first = this.space === undefined;
      this.space = space.id; this.pending = null;
      if (!(first && !(space.id in this.panels))) {
        const stored = this.panels[space.id] ?? null, want = enabled.includes(stored) ? stored : null;
        if (want !== now) {
          this.pending = { want, until: Date.now() + 1000 };
          if (want) { run("layout.select", { stack: "panel-body", child: want }); run("layout.show", { id: "panel" }); }
          else run("layout.hide", { id: "panel" });
          return;
        }
      }
    }
    // Until the restore lands (or something else won), the old state isn't a choice.
    if (this.pending) {
      if (this.pending.want !== now && Date.now() < this.pending.until) return;
      this.pending = null;
    }
    if (this.panels[space.id] === now) return;
    this.panels[space.id] = now;
    localStorage.setItem("panels", JSON.stringify(this.panels));
  }

  render() {
    const t = theme();
    const space = spaces().find(p => p.active);
    const shown = space?.tabs ?? [];
    const stop = (_e, cx) => cx.stop_propagation();
    const button = (id, label, action) => div().id(id).size(30).flex_none().tooltip(id === "tab-new" ? "新建标签" : id).flex().items_center().justify_center().rounded(6).text_color(t.dim).hover(s => s.bg(t.hover).text_color(t.foreground))
      .on_mouse_down("left", stop).on_click(action).child(label);
    const item = (c, i) => {
      const program = panes().find(p => p.tab === c.id && p.program?.agent)?.program ?? panes().find(p => p.tab === c.id)?.program;
      const name = /^tb\d+$/.test(c.name) ? program?.name ?? "Terminal" : c.name;
      const labelWidth=Math.min(128,Array.from(name).reduce((w,ch)=>w+(/^[\x00-\x7f]$/.test(ch)?7:13),0));
      const tabWidth=Math.max(136,Math.ceil((96+labelWidth)/8)*8);
      return h_flex().id(`tab-${c.id}`).relative().w(tabWidth).h(40).px(12).gap(8).rounded(0).items_center().flex_none().text_size(12.8)
        .text_color(c.active ? t.foreground : t.muted)
        .child(image(`mods/ink-chrome/art/bamboo-v17-${tabWidth}.png`).absolute().inset(0).size_full().opacity(c.active ? 1 : this.hovered === c.id ? 0.85 : 0.52))
        .on_hover((on,cx) => { this.hovered = on ? c.id : this.hovered === c.id ? null : this.hovered; cx.notify(); })
        .hover(s => s.bg(t.hover))
        .on_mouse_down("left", (e, cx) => { cx.stop_propagation(); this.pressed = i; if (e.click_count === 2) run("tab.rename", { id: c.id }); })
        .on_mouse_up("left", () => {
          const from = this.pressed; this.pressed = null;
          if (from !== null && from !== i) run("tab.move", { id: shown[from].id, index: space.tabs.findIndex(x => x.id === c.id) + 1 });
          else run("tab.select", { id: c.id });
        })
        .on_mouse_down("right", (_e, cx) => { cx.stop_propagation(); openOverlay({ mod: "menu", kind: "popup", width: 200, props: { tab: "tab", target: { id: c.id, space: space.id } } }); })
        .child(i < 15 ? image(`mods/ink-chrome/art/ink-number-v11-${i+1}.png`).relative().w(20).h(18).flex_none().opacity(.78).tooltip(`标签 ${i+1}`) : div().relative().w(20).flex_none().text_size(11).child(String(i+1)))
        .child(div().relative().flex_1().min_w(0).font_family("LXGW WenKai Mono").text_size(14).tooltip(name).truncate().child(c.zoomed ? `${name} Z` : name))
        .when(c.active, el => el.child(image("mods/ink-chrome/art/stroke-v3.png").absolute().left(18).right(18).bottom(1).h(4).opacity(0.7)))
        .child(h_flex().id(`tab-actions-${c.id}`).relative().flex_none().gap(6).items_center()
          .child(div().id(`tab-status-${c.id}`).size(16).flex_none().flex().items_center().justify_center()
            .when(c.status === "working", el => el.child(svg("mods/ink-chrome/art/ink-ring-v9.svg").size(12).flex_none().text_color(t.working).spin(1600)))
            .when(c.status === "blocked", el => el.child(inkStamp("待",t.blocked).tooltip("待确认")))
            .when(c.status === "done", el => el.child(svg("mods/ink-chrome/art/check-v2.svg").size(13).flex_none().text_color(t.done).tooltip("已完成"))))
          .child(div().relative().id(`close-${c.id}`).size(18).flex_none().flex().items_center().justify_center().tooltip("关闭标签").opacity(c.active || this.hovered === c.id ? 1 : 0).text_color(t.dim).on_mouse_down("left", stop).on_click((_e, cx) => { cx.stop_propagation(); run(c.active || this.hovered === c.id ? "tab.close" : "tab.select", { id: c.id }); }).child(svg("mods/pane/close.svg").size(12))));
    };
    const root = layout(), sidebar = find(root, "sidebar"), w = window();
    // Old saved rails and a dragged-narrow sidebar can be smaller than the window buttons.
    const lightsPadding = w?.platform === "macos" && w.titlebar === "none" && !w.fullscreen && root?.traffic_lights
      ? Math.max(10, (root.traffic_lights[0] + 64) / settings().zoom - (sidebar?.hidden ? 0 : sidebar?.size?.px ?? 0))
      : 10;
    const panel = find(root, "panel"), body = find(root, "panel-body");
    const enabled = shared("workspace.panels") ?? ["files", "changes"];
    this.syncPanel(space, panel, body, enabled);
    const panelButton = (id, label, icon) => {
      const on = panel && !panel.hidden && body?.active === id;
      return h_flex().id(`panel-${id}`).h(32).px(10).gap(6).flex_none().items_center().rounded(1)
        .text_size(12).bg(on ? t.selected : t.chrome).text_color(on ? t.foreground : t.muted)
        .hover(s => s.bg(t.hover)).on_mouse_down("left", stop)
        .on_click(() => {
          if (on) run("layout.hide", { id: "panel" });
          else { run("layout.select", { stack: "panel-body", child: id }); run("layout.show", { id: "panel" }); }
        }).child(svg(icon).size(14)).child(label);
    };
    return h_flex().size_full().min_w(0).px(16).pl(lightsPadding).gap(6).items_center().bg(t.chrome).relative().child(inkLine("bottom"))
      .on_mouse_up("left", () => { this.pressed = null; })
      .on_scroll_wheel(e => { if (Math.abs(e.delta.y) >= 1) run(e.delta.y > 0 ? "tab.prev" : "tab.next"); })
      .child(h_flex().id("tab-scroll").flex_1().min_w(0).h_full().items_center().gap(3).overflow_x_scrollbar().children(shown.map(item)))
      .child(button("tab-new", "+", () => openOverlay({ mod: "new-menu", kind: "popup", width: 250, height: 512 })))
      .when(enabled.includes("files"), el => el.child(panelButton("files", "文件", "mods/files/file.svg")))
      .when(enabled.includes("changes"), el => el.child(panelButton("changes", "变更", "mods/changes/changes.svg")))
      .when(w?.buttons, el => el.child(button("minimize", w.platform === "windows" ? svg("mods/tabs/win-min.svg").size(16) : "−", () => run("window.minimize")))
        .child(button("maximize", w.platform === "windows" ? svg(`mods/tabs/${w.maximized ? "win-restore" : "win-max"}.svg`).size(16) : "□", () => run("window.maximize")))
        .child(button("close-window", w.platform === "windows" ? svg("mods/tabs/win-close.svg").size(16) : svg("mods/pane/close.svg").size(13), () => run("window.close"))));
  }
}
