import { image } from "gpui-kit";
import { shared, setShared } from "herdr";

const OBJECTS = [
  ["go-black", "墨棋"], ["brush", "毛笔"], ["scroll", "书卷"],
  ["inkstone", "砚台"], ["fan", "折扇"], ["cup", "茶盏"],
  ["seal", "印章"], ["gourd", "葫芦"], ["flute", "竹笛"],
  ["lantern", "纸灯"], ["go-white", "玉棋"], ["book", "线装书"],
  ["paperweight", "镇纸"], ["lotus", "莲盏"], ["pouch", "香囊"],
];
const STORAGE = ["ink", "workspace", "objects", "v15"].join(".");

// Both sidebar mods share assignments by space ID, independent of sort and names.
export function spaceObjects(spaces) {
  const stored = shared(STORAGE);
  const slots = stored && typeof stored === "object" && !Array.isArray(stored) ? { ...stored } : {};
  const valid = value => Number.isInteger(value) && value >= 0 && value < OBJECTS.length;
  const used = new Set(spaces.map(s => slots[s.id]).filter(valid));
  let changed = false;
  for (const space of spaces) {
    if (valid(slots[space.id])) continue;
    let slot = OBJECTS.findIndex((_, i) => !used.has(i));
    if (slot < 0) slot = Object.keys(slots).length % OBJECTS.length;
    slots[space.id] = slot;
    used.add(slot);
    changed = true;
  }
  if (changed) setShared(STORAGE, slots);
  return slots;
}

export function spaceObject(id, name, slots, size = 24) {
  const [file, label] = OBJECTS[slots[id] ?? 0];
  return image(`mods/ink-chrome/art/object-v16-${file}.png`)
    .w(size).h(size).flex_none()
    .tooltip(`${name || "工作区"} · ${label}`)
    .accessibility_label(`${name || "工作区"}，${label}`);
}
