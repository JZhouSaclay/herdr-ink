import { scrollPaper } from "./scroll.js";
import { inkLine } from "./ink.js";
// A lazy file browser for the focused pane's folder: text files open in an editor that saves
// back to disk (bounded previews for everything else).
import { View, div, svg, image } from "gpui-kit";
import { v_flex, h_flex, Editor, EditorState, TextView } from "gpui-base";
import { spaces, panes, focused, exec, readTextFile, writeTextFile, watchFolder, theme, settings, window, appHome, nextCommand } from "herdr";

function location() {
  const space = spaces().find(s => s.active), f = focused();
  const pane = f?.pane ? panes().find(p => p.pane === f.pane) : null;
  const on = f?.pane === null ? (f.terminal?.includes("/") ? f.terminal.split("/")[0] : null) : space?.machine ?? null;
  return { cwd: pane?.cwd || f?.cwd || space?.folder, on, space: space?.id };
}
const key = () => JSON.stringify(location());
const LANG = { ts: "js", tsx: "js", mts: "js", cts: "js", jsx: "js", mjs: "js", toml: "yaml", jsonc: "json", svelte: "html", vue: "html" };
const PER_FOLDER = 500, TOTAL = 5000, MAX_EDIT = 400000;
const IMAGES = new Set(["png", "jpg", "jpeg", "jpe", "jfif", "webp", "gif", "bmp", "tif", "tiff", "ico", "avif", "svg"]);
const MARKDOWN = new Set(["md", "markdown", "mdown", "mkd", "mkdn"]);
const PYTHON = "/opt/homebrew/bin/python3";
const extension = path => path.split(/[\\/]/).pop().split(".").pop().toLowerCase();
const sourcePath = (root, path) => /^(?:[\\/]|[a-z]:[\\/])/i.test(path) ? path : `${root}/${path}`;

async function visualPreview(source, page, machine) {
  const args = [`${appHome()}/mods/ink-files/preview.py`, "--app-home", appHome(), "--source", source, "--page", String(page)];
  if (machine) args.push("--machine", machine);
  const result = await exec(PYTHON, args);
  if (!result.stdout.trim()) throw new Error(result.stderr.trim() || "Cannot render this preview");
  const preview = JSON.parse(result.stdout);
  if (result.code !== 0 || preview.error) throw new Error(preview.error || result.stderr.trim() || "Cannot render this preview");
  return preview;
}

function control(id, label, enabled, action, t) {
  return div().id(id).h(26).min_w(26).px(6).flex_none().flex().items_center().justify_center().rounded(5)
    .text_color(enabled ? t.foreground : t.dim).child(label)
    .when(enabled, el => el.cursor_pointer().hover(s => s.bg(t.hover)).on_click((_e, cx) => action(cx)));
}

async function directory(path, on) {
  const windowsDirectory = async () => {
    // Windows PowerShell otherwise uses the console code page; exec decodes UTF-8.
    // Links keep directory attributes even when dangling; check their target.
    // Other reparse points (OneDrive's folders) have no LinkType and are folders.
    // PowerShell reads curly single quotes as quotes too, so they're doubled like '.
    const r = await exec("powershell", ["-NoProfile", "-Command", "[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false); & { param($p) @(Get-ChildItem -LiteralPath $p -Force -ErrorAction Stop | Where-Object Name -ne '.git' | Select-Object -First 501 | ForEach-Object { @{ name=$_.Name; dir=($_.PSIsContainer -and (-not ($_.Attributes -band [IO.FileAttributes]::ReparsePoint) -or -not $_.LinkType -or ($_.Target -and [IO.Directory]::Exists(([IO.Path]::Combine([IO.Path]::GetDirectoryName($_.FullName), $_.Target[0])))))) } }) | ConvertTo-Json -Compress } '" + path.replace(/['‘’‚‛]/g, "$&$&") + "'"], { on });
    if (r.code !== 0) throw new Error(r.stderr || "Cannot list this folder");
    const result = JSON.parse(r.stdout || "[]");
    return Array.isArray(result) ? result : [result];
  };
  if (!on && window()?.platform === "windows") return windowsDirectory();
  const script = 'n=0; for p in "$1"/* "$1"/.[!.]* "$1"/..?*; do [ -e "$p" ] || [ -L "$p" ] || continue; name=${p##*/}; [ "$name" = .git ] && continue; if [ -d "$p" ]; then kind=d; else kind=f; fi; printf "%s\\0%s\\0" "$kind" "$name"; n=$((n+1)); [ "$n" -gt 500 ] && break; done; test -d "$1"';
  let r;
  try { r = await exec("sh", ["-c", script, "files", path], { on }); }
  catch (e) {
    if (on && String(e).includes("cannot start sh: program not found")) return windowsDirectory();
    throw e;
  }
  if (r.code !== 0) throw new Error(r.stderr || "Cannot list this folder");
  const fields = r.stdout.split("\0"), out = [];
  for (let i = 0; i + 1 < fields.length; i += 2) out.push({ name: fields[i + 1], dir: fields[i] === "d" });
  return out;
}

export default class Files extends View {
  init(_props, cx) {
    this.saved = new Map();
    this.handle = cx.focus_handle();
    this.entries = new Map(); this.folders = new Set(); this.pending = new Set(); this.marks = {};
    this.refresh(cx);
    cx.timer.every(10000, cx => this.refresh(cx));
    cx.timer.every(400, cx => this.autosave(cx));
    cx.spawn(async cx => {
      for (;;) {
        const command = await nextCommand();
        if (command.startsWith("open:")) this.show(command.slice(5), cx);
        else if (command === "back") this.show(null, cx);
        else if (command === "markdown-toggle") this.toggleMarkdown(cx);
        else if (command === "page-next") this.turnPage(1, cx);
        else if (command === "page-prev") this.turnPage(-1, cx);
        else if (command === "zoom-in") this.changeZoom(1, cx);
        else if (command === "zoom-out") this.changeZoom(-1, cx);
        else if (command === "fit") this.zoom = 1;
        cx.notify();
      }
    });
  }

  watch(root, cx) {
    if (this.on || this.watched === root) return;
    this.watched = root;
    const context = this.context;
    cx.spawn(async cx => {
      try { while (this.context === context) { await watchFolder(root); if (this.current(context)) this.refresh(cx); } }
      catch { if (this.context === context) this.watched = null; }
    });
  }

  current(context) {
    return this.context === context && key() === context.key;
  }

  async loadFolder(path, context) {
    const { on, cwd: root } = context;
    const entries = await directory(path ? `${root}/${path}` : root, on);
    if (!this.current(context) || (path && !this.folders.has(path))) return;
    const used = [...this.entries.entries()].filter(([p]) => p !== path).reduce((n, [, e]) => n + e.length, 0);
    this.entries.set(path, entries.slice(0, Math.max(0, Math.min(PER_FOLDER, TOTAL - used))).sort((a, b) => Number(b.dir) - Number(a.dir) || a.name.localeCompare(b.name)));
    if (entries.length > PER_FOLDER || used + entries.length > TOTAL) this.limited = true;
  }

  refresh(cx) {
    const { cwd, on } = location(), next = key();
    if (next !== this.context?.key) {
      if (this.context) this.saved.set(this.context.key, { folders: this.folders, file: this.file });
      const saved = this.saved.get(next);
      this.context = { key: next, cwd, on }; this.root = cwd; this.on = on; this.entries = new Map(); this.folders = new Set(saved?.folders);
      this.pending = new Set(); this.marks = {}; this.show(null, cx); this.watched = null; this.error = null; this.limited = false;
      this.loading = false;
      if (saved?.file) this.show(saved.file, cx);
    }
    if (!cwd || this.loading) return;
    const context = this.context;
    this.loading = true;
    this.limited = false;
    cx.spawn(async cx => {
      try {
        for (const path of ["", ...this.folders]) {
          if (!this.current(context)) return;
          await this.loadFolder(path, context);
        }
        const top = await exec("git", ["rev-parse", "--show-toplevel"], { cwd, on }).catch(() => null);
        const marks = {};
        if (top?.code === 0) {
          // Writes nothing under .git (index lock, fsmonitor cookie): the folder watch would refresh again.
          const status = await exec("git", ["--no-optional-locks", "-c", "core.fsmonitor=false", "status", "--porcelain=v1", "-z", "--no-renames", "--untracked-files=all"], { cwd, on }).catch(() => null);
          if (status?.code === 0) for (const entry of status.stdout.split("\0").filter(Boolean).slice(0, TOTAL)) {
            const xy = entry.slice(0, 2);
            marks[`${top.stdout.trim()}/${entry.slice(3)}`] = xy === "??" || xy.includes("A") ? "A" : xy.includes("U") ? "U" : xy.includes("D") ? "D" : "M";
          }
        }
        if (!this.current(context)) return;
        this.marks = marks; this.error = null; this.watch(cwd, cx);
      } catch (e) { if (this.current(context)) this.error = String(e); }
      finally { if (this.context === context) this.loading = false; cx.notify(); }
    });
  }

  toggle(path, cx) {
    if (this.folders.has(path)) {
      for (const folder of [...this.folders]) if (folder === path || folder.startsWith(path + "/")) {
        this.folders.delete(folder);
        this.entries.delete(folder);
      }
    } else {
      this.folders.add(path);
      if (!this.entries.has(path) && !this.pending.has(path)) {
        const context = this.context;
        this.pending.add(path);
        cx.spawn(async cx => {
          try { await this.loadFolder(path, context); }
          catch (e) { if (this.current(context)) this.error = String(e); }
          finally { if (this.context === context) this.pending.delete(path); cx.notify(); }
        });
      }
    }
    cx.notify();
  }

  show(path, cx) {
    this.flush(cx);
    this.code?.release(); this.code = null; this.file = path; this.fileError = null;
    this.original = null; this.editable = false; this.dirty = false; this.saving = false; this.notice = null; this.failed = false;
    this.preview = null; this.previewKind = null; this.previewLoading = false; this.page = 1; this.pageCount = 0; this.zoom = 1;
    this.markdownPreview = false;
    const request = this.previewRequest = {};
    if (!path || !cx) return;
    const context = this.context, root = this.root, on = this.on, ext = extension(path);
    this.previewKind = ext === "pdf" ? "pdf" : IMAGES.has(ext) ? "image" : null;
    if (this.previewKind) { this.loadVisual(cx); return; }
    cx.spawn(async cx => {
      try {
        const text = await readTextFile(sourcePath(root, path), { on });
        if (this.previewRequest !== request || !this.current(context)) return;
        if (text === null) { this.fileError = "This file is no longer available"; return; }
        if (text.includes("\0")) { this.fileError = "Binary file · no text preview"; return; }
        const t = theme(), large = text.length > MAX_EDIT;
        // writeTextFile writes this machine only, and a truncated text must never be saved back.
        this.editable = !on && !large;
        this.original = this.editable ? text : null;
        this.code = EditorState.new({ language: LANG[ext] ?? ext, readonly: !this.editable, soft_wrap: true,
          value: large ? text.slice(0, MAX_EDIT) + "\n… (file truncated)" : text,
          font_family: settings().font_family, font_size: 12,
          syntax: { keyword: t.ansi5, string: t.ansi2, comment: t.dim, function: t.ansi4, type: t.ansi3, number: t.ansi1, constant: t.ansi6 } });
        if (this.editable) this.code.on("change", () => {
          this.changedAt = Date.now();
          if (this.dirty) return;
          this.dirty = true; this.notice = null; cx.notify();
        });
        else this.notice = on ? `Read-only on ${on}` : "Too large to edit";
      } catch (error) { if (this.previewRequest === request && this.current(context)) this.fileError = String(error); }
      finally { cx.notify(); }
    });
  }

  // Writes once the typing stopped, and once more when the file is left: the draft lives in the
  // editor state, which the next file replaces.
  autosave(cx) {
    if (!this.dirty || this.saving || this.failed || !this.editable) return;
    if (Date.now() - this.changedAt < 700) return;
    this.save(cx);
  }

  flush(cx) {
    if (!cx || !this.dirty || this.saving || !this.code || !this.editable) return;
    this.save(cx);
  }

  save(cx) {
    if (!this.code || !this.editable || this.saving) return;
    const value = this.code.value();
    // expected: the text read from disk, so a file changed behind us is refused, not overwritten.
    if (value === this.original) { this.dirty = false; cx.notify(); return; }
    const context = this.context, path = this.file, expected = this.original;
    this.saving = true; this.notice = null; cx.notify();
    cx.spawn(async cx => {
      try {
        await writeTextFile(sourcePath(this.root, path), value, expected);
        if (this.file !== path || !this.current(context)) return;
        this.original = value; this.dirty = false; this.failed = false;
      } catch (error) {
        if (this.file !== path || !this.current(context)) return;
        this.failed = true; this.dirty = true;
        this.notice = `Cannot save: ${String(error).replace(/^Error: '[^']*': /, "")}`;
      } finally { this.saving = false; cx.notify(); }
    });
  }

  loadVisual(cx) {
    const context = this.context, source = sourcePath(this.root, this.file), page = this.page;
    const request = this.previewRequest = {};
    this.preview = null; this.previewLoading = true; this.fileError = null; this.previewProgress = null;
    cx.spawn(async cx => {
      try {
        for (;;) {
          const preview = await visualPreview(source, page, context.on);
          if (this.previewRequest !== request || !this.current(context)) return;
          if (preview.pending) {
            this.previewProgress = `Downloading preview… ${Math.floor(preview.received / preview.total * 100)}%`;
            cx.notify();
            continue;
          }
          this.preview = preview; this.pageCount = preview.pages;
          break;
        }
      } catch (error) {
        if (this.previewRequest === request && this.current(context)) this.fileError = String(error);
      } finally {
        if (this.previewRequest === request) this.previewLoading = false;
        cx.notify();
      }
    });
  }

  turnPage(delta, cx) {
    if (this.previewKind !== "pdf" || this.previewLoading || !this.pageCount) return;
    const page = Math.max(1, Math.min(this.pageCount, this.page + delta));
    if (page === this.page) return;
    this.page = page;
    this.loadVisual(cx);
  }

  changeZoom(direction, cx) {
    if (!this.previewKind) return;
    this.zoom = Math.max(0.25, Math.min(4, Math.round(this.zoom * (direction > 0 ? 1.25 : 0.8) * 100) / 100));
    cx.notify();
  }

  toggleMarkdown(cx) {
    if (!this.file || !MARKDOWN.has(extension(this.file)) || !this.code) return;
    if (!this.markdownPreview) this.flush(cx);
    this.markdownPreview = !this.markdownPreview;
    cx.notify();
  }

  renderMarkdown(t) {
    return TextView.markdown("files-markdown-preview", this.code.value())
      .flex_1().min_h(0).min_w(0).w_full().p(16).text_size(13).text_color(t.foreground)
      .selectable(true).scrollable(true);
  }

  renderVisual(t) {
    const preview = this.preview, busy = this.previewLoading;
    const width = Math.max(32, (this.panelSize?.width ?? 300) - 36);
    const height = Math.max(32, (this.panelSize?.height ?? 600) - 112);
    const scale = preview ? Math.min(width / preview.width, height / preview.height) * this.zoom : 1;
    return v_flex().flex_1().min_h(0).min_w(0)
      .child(h_flex().h(36).flex_none().px(8).gap(2).items_center().border_b(1).border_color(t.border).text_size(12)
        .when(this.previewKind === "pdf", el => el
          .child(control("files-page-prev", "‹", !busy && this.page > 1, cx => this.turnPage(-1, cx), t))
          .child(div().flex_none().text_color(t.muted).child(`${this.page} / ${this.pageCount || "…"}`))
          .child(control("files-page-next", "›", !busy && this.page < this.pageCount, cx => this.turnPage(1, cx), t)))
        .child(div().flex_1())
        .child(control("files-zoom-out", "−", this.zoom > 0.25, cx => this.changeZoom(-1, cx), t))
        .child(control("files-fit", this.zoom === 1 ? "Fit" : `${Math.round(this.zoom * 100)}%`, true, cx => { this.zoom = 1; cx.notify(); }, t))
        .child(control("files-zoom-in", "+", this.zoom < 4, cx => this.changeZoom(1, cx), t)))
      .child(div().id(`files-preview-${this.page}-${this.zoom}`).flex_1().min_h(0).min_w(0).overflow_scrollbar().bg(t.canvas)
        .child(v_flex().min_w_full().min_h_full().p(12).items_center().justify_center()
          .when(Boolean(preview), el => el.child(image(preview.asset).w(Math.max(1, Math.round(preview.width * scale))).h(Math.max(1, Math.round(preview.height * scale))).flex_none()))
          .when(!preview, el => el.child(div().p(12).text_size(12).text_color(t.muted).child(this.fileError || (busy ? this.previewProgress || "Loading preview…" : "Preview unavailable"))))
          .when(Boolean(this.fileError), el => el.child(control("files-preview-retry", "Retry", !busy, cx => this.loadVisual(cx), t)))));
  }

  rows(prefix, depth, out, t) {
    if (out.length >= TOTAL || depth > 40) return out;
    for (const entry of this.entries.get(prefix) ?? []) {
      if (out.length >= TOTAL) break;
      const path = prefix ? `${prefix}/${entry.name}` : entry.name, open = this.folders.has(path), mark = this.marks[`${this.root}/${path}`];
      out.push(h_flex().id(`file-${path}`).h(28).flex_none().pl(8 + depth * 18).pr(8).gap(7).items_center().rounded(7).cursor_pointer().hover(s => s.bg(t.hover))
        .on_click((_e, cx) => entry.dir ? this.toggle(path, cx) : this.show(path, cx))
        .child(entry.dir ? svg(`mods/ink-files/chevron-${open ? "down" : "right"}.svg`).size(12).flex_none().text_color(t.dim) : div().w(12).flex_none())
        .child(svg(`mods/ink-files/${entry.dir ? "folder" : "file"}.svg`).size(14).flex_none().text_color(t.muted))
        .child(div().flex_1().min_w(0).truncate().child(entry.name))
        .when(Boolean(mark), el => el.child(div().text_size(11).text_color(mark === "A" ? t.ansi2 : mark === "D" || mark === "U" ? t.ansi1 : t.blocked).child(mark))));
      if (entry.dir && open) this.rows(path, depth + 1, out, t);
    }
    return out;
  }

  render(cx) {
    if (key() !== this.context?.key) this.refresh(cx);
    const t = theme();
    return scrollPaper(this, "ink-files-scroll", v_flex().id("files").size_full().min_w(0).min_h(0).overflow_hidden().font_family("LXGW WenKai Mono").text_color(t.foreground).text_size(13)
      .on_size_change((size, cx) => { this.panelSize = size; cx.notify(); })
      .track_focus(this.handle)
      .on_key_down((e, cx) => {
        if (e.keystroke === "cmd-s") { cx.stop_propagation(); this.save(cx); }
      })
      .child(h_flex().h(42).flex_none().px(14).gap(8).items_center().relative().child(inkLine("bottom", .65))
        .when(Boolean(this.file), el => el.child(div().id("files-back").w(20).cursor_pointer().text_color(t.muted).on_click((_e, cx) => { this.show(null, cx); cx.notify(); }).child("←")))
        .child(div().font_semibold().child("文件"))
        .when(this.dirty, el => el.child(div().text_size(11).text_color(t.dim).child("●")))
        .child(div().flex_1().min_w(0).truncate().text_right().text_size(12).text_color(this.dirty ? t.foreground : t.dim).child(this.file ?? this.root?.split(/[\\/]/).pop() ?? ""))
        .when(this.file && MARKDOWN.has(extension(this.file)), el => el.child(control("files-markdown-toggle", this.markdownPreview ? "Source" : "Preview", Boolean(this.code), cx => this.toggleMarkdown(cx), t))))
      .when(Boolean(this.notice), el => el.child(h_flex().flex_none().px(12).py(5).gap(8).items_center().border_b(1).border_color(t.border).text_size(11).text_color(t.muted)
        .child(div().flex_1().min_w(0).child(this.notice))
        .when(this.failed, el => el.child(control("files-reload", "Reload", !this.saving, cx => this.show(this.file, cx), t)))))
      .when(!this.file, el => el.child(v_flex().id("files-tree").flex_1().min_h(0).overflow_y_scrollbar().p(6).children(this.rows("", 0, [], t))
        .when(Boolean(this.error) || !this.entries.get("")?.length, el => el.child(div().p(8).text_size(12).text_color(t.dim).child(this.error || (this.loading ? "Loading files…" : this.root ? "No files" : "No folder"))))
        .when(this.limited, el => el.child(div().p(8).text_size(11).text_color(t.dim).child("File list limited to 500 entries per folder and 5,000 total")))))
      .when(Boolean(this.file), el => el.child(this.previewKind ? this.renderVisual(t) : this.markdownPreview && this.code ? this.renderMarkdown(t) : this.code ? Editor.new(this.code).flex_1().min_w(0).min_h(0).bg("#f8f9f5") : div().p(12).text_color(t.dim).child(this.fileError || "Loading file…"))));
  }
}
