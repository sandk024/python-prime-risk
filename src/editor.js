import { EditorView, keymap, lineNumbers, highlightActiveLine, drawSelection } from "@codemirror/view";
import { EditorState } from "@codemirror/state";
import { defaultKeymap, history, historyKeymap, indentWithTab, undo, redo, indentMore, indentLess, cursorCharLeft, cursorCharRight, cursorLineUp, cursorLineDown } from "@codemirror/commands";
import { python } from "@codemirror/lang-python";
import { syntaxHighlighting, HighlightStyle, indentOnInput, bracketMatching, indentUnit } from "@codemirror/language";
import { tags as t } from "@lezer/highlight";

const hl = HighlightStyle.define([
  { tag: t.keyword, color: "var(--hl-kw)" },
  { tag: [t.string, t.special(t.string)], color: "var(--hl-str)" },
  { tag: t.comment, color: "var(--hl-com)", fontStyle: "italic" },
  { tag: [t.number, t.bool, t.null], color: "var(--hl-num)" },
  { tag: [t.function(t.variableName), t.function(t.propertyName)], color: "var(--hl-fn)" },
  { tag: t.definition(t.variableName), color: "var(--hl-def)" },
  { tag: [t.operator], color: "var(--hl-op)" },
]);

const theme = EditorView.theme({
  "&": { fontSize: "15px", backgroundColor: "var(--code-bg)", color: "var(--code-fg)", borderRadius: "10px" },
  ".cm-content": { fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace", padding: "8px 0", caretColor: "var(--accent)" },
  ".cm-gutters": { backgroundColor: "var(--code-bg)", color: "var(--muted)", border: "none", borderRadius: "10px 0 0 10px" },
  ".cm-activeLine": { backgroundColor: "var(--code-active)" },
  ".cm-activeLineGutter": { backgroundColor: "transparent" },
  "&.cm-focused": { outline: "2px solid var(--accent)" },
  ".cm-cursor": { borderLeftColor: "var(--accent)", borderLeftWidth: "2px" },
  ".cm-selectionBackground, &.cm-focused .cm-selectionBackground": { backgroundColor: "var(--code-sel) !important" },
});

export function createEditor(parent, doc, { onChange, onFocus, onBlur } = {}) {
  const view = new EditorView({
    parent,
    state: EditorState.create({
      doc,
      extensions: [
        lineNumbers(), history(), drawSelection(), highlightActiveLine(), indentOnInput(), bracketMatching(),
        indentUnit.of("    "), EditorState.tabSize.of(4), python(), syntaxHighlighting(hl), theme,
        EditorView.lineWrapping,
        keymap.of([...defaultKeymap, ...historyKeymap, indentWithTab]),
        EditorView.contentAttributes.of({ autocapitalize: "off", autocorrect: "off", spellcheck: "false", autocomplete: "off", "data-gramm": "false" }),
        EditorView.updateListener.of(u => { if (u.docChanged && onChange) onChange(u.state.doc.toString()); }),
        EditorView.domEventHandlers({ focus: () => onFocus && onFocus(view), blur: () => onBlur && onBlur(view) }),
      ],
    }),
  });
  return view;
}

export function getText(view) { return view.state.doc.toString(); }
export function setText(view, text) { view.dispatch({ changes: { from: 0, to: view.state.doc.length, insert: text } }); }
export function insert(view, text, back = 0) {
  const r = view.state.selection.main;
  view.dispatch({ changes: { from: r.from, to: r.to, insert: text }, selection: { anchor: r.from + text.length - back }, scrollIntoView: true });
  view.focus();
}
export const commands = { undo, redo, indentMore, indentLess, left: cursorCharLeft, right: cursorCharRight, up: cursorLineUp, down: cursorLineDown };
export function exec(view, name) { commands[name](view); view.focus(); }
