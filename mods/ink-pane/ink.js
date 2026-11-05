import { div, svg, PathBuilder } from "gpui-kit";
// Run coverage is sampled from the original ink scan, rather than a straight rule.
const bands = [[[295,298,0],[335,344,0],[41,118,1],[122,353,1],[40,353,2],[20,364,3],[14,373,4],[14,275,5],[278,282,5],[292,293,5],[294,298,5]],[[44,102,1],[153,157,1],[199,348,1],[41,347,2],[30,353,3],[17,359,4],[16,120,5],[168,237,5]],[[60,87,1],[250,275,1],[284,306,1],[311,314,1],[337,339,1],[342,344,1],[43,117,2],[119,322,2],[47,241,3],[261,267,3],[272,279,3],[283,315,3],[316,318,3],[325,337,3],[19,347,4],[34,64,5]]];
const cache = {};
function paths(vertical) {
  const key = vertical ? "v" : "h";
  if (cache[key]) return cache[key];
  return cache[key] = bands.map(runs => {
    const p = PathBuilder.fill();
    for (const [a,b,y] of runs) {
      const lo = `${a/384*100}%`, hi = `${b/384*100}%`;
      const n = .25+y*.5, m=n+.55;
      if (vertical) p.move_to(n,lo).line_to(m,lo).line_to(m,hi).line_to(n,hi).close();
      else p.move_to(lo,n).line_to(hi,n).line_to(hi,m).line_to(lo,m).close();
    }
    return p.build();
  });
}
export function inkLine(edge="bottom", opacity=.85) {
  const vertical=edge==="left" || edge==="right";
  let box=div().absolute();
  if (vertical) box=box.top(0).bottom(0).w(4);
  else box=box.left(0).right(0).h(4);
  if(edge==="top") box=box.top(0);
  if(edge==="bottom") box=box.bottom(0);
  if(edge==="left") box=box.left(0);
  if(edge==="right") box=box.right(0);
  return box.children(paths(vertical).map((p,i)=>window.paint_path(p,"#506258"+Math.round(255*opacity*[.12,.15,.18][i]).toString(16).padStart(2,"0")).absolute().inset(0).size_full()));
}
export function inkStamp(label,color) {
  return div().relative().size(17).flex_none().flex().items_center().justify_center().text_color(color)
    .child(svg("mods/ink-chrome/art/ink-seal-v9.svg").absolute().inset(0).size_full().opacity(.65))
    .child(div().relative().font_family("LXGW WenKai Mono").text_size(11.5).child(label));
}
