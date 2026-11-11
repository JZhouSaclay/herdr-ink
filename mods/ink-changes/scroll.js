import { div, image } from "gpui-kit";
const art = "mods/ink-chrome/art/scroll-";

// Paint only. These layers are behind the interactive content, never overlays
// across its hit targets. Fixed-size caps and tiled spans survive panel resizing.
export function scrollPaper(view, id, content) {
  const width = view.scrollSize?.width ?? 368, height = view.scrollSize?.height ?? 900;
  const axis = end => div().absolute().left(0).right(0).h(24)
    .when(end === "top", e => e.top(0)).when(end === "bottom", e => e.bottom(0))
    .child(div().absolute().left(28).right(28).top(0).h(24).overflow_hidden()
      .children(Array.from({length:Math.max(1,Math.ceil((width-56)/240))},(_,i) =>
        image(`${art}${end}-mid-v25.png`).absolute().left(i*240).top(0).w(240).h(24))))
    .child(image(`${art}${end}-left-v25.png`).absolute().left(0).top(0).w(28).h(24))
    .child(image(`${art}${end}-right-v25.png`).absolute().right(0).top(0).w(28).h(24));
  const edge = side => div().absolute().top(16).bottom(16).w(8).overflow_hidden()
    .when(side === "left", e => e.left(8)).when(side === "right", e => e.right(8))
    .children(Array.from({length:Math.max(1,Math.ceil((height-32)/96))},(_,i) =>
      image(`${art}${side}-v25.png`).absolute().top(i*96).left(0).w(8).h(96)));
  return div().id(id).relative().size_full().min_w(0).min_h(0).overflow_hidden()
    .on_size_change((size,cx) => {
      if (size.width <= 0 || size.height <= 0) return;
      const next={width:Math.round(size.width),height:Math.round(size.height)};
      if(next.width!==view.scrollSize?.width || next.height!==view.scrollSize?.height){view.scrollSize=next;cx.notify();}
    })
    .child(div().absolute().left(12).right(12).top(16).bottom(16).bg("#f8f9f5"))
    .child(edge("left")).child(edge("right")).child(axis("top")).child(axis("bottom"))
    .child(div().absolute().left(20).right(20).top(28).bottom(28).min_w(0).min_h(0).child(content));
}
