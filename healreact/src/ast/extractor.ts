/**
 * L1 — AST extractor.
 *
 * Walks a React/TSX source tree with ts-morph and emits a LocatorSheet:
 * one record per interactive JSX element, capturing the stable anchors
 * that L3 (LLM healer) can use as fallback rungs and that the runtime
 * `intent(...)` helper resolves at execution time.
 *
 * Intent-label assignment is intentionally NOT done here — this file is
 * a pure static extractor with zero LLM dependency. The intent labeller
 * (src/ast/intent_labeller.ts) reads this sheet and adds the `intent`
 * field via an LLM call, so this stage can run offline / in CI.
 *
 * Usage:
 *   tsx src/ast/extractor.ts --src <react-src-dir> [--out LocatorSheet.json]
 */
import { Project, SyntaxKind, JsxOpeningElement, JsxSelfClosingElement, Node } from "ts-morph";
import { writeFileSync, mkdirSync, existsSync } from "node:fs";
import { dirname, relative, resolve } from "node:path";

interface LocatorRecord {
  componentFile: string;          // relative path
  componentName: string | null;   // enclosing function/class component name
  elementTag: string;             // 'button', 'input', 'Button', ...
  line: number;
  column: number;
  // Stable anchor candidates (any may be null):
  role: string | null;            // ARIA role (explicit or implicit from tag)
  ariaLabel: string | null;       // aria-label or aria-labelledby ref
  testId: string | null;          // data-testid value
  dataIntent: string | null;      // data-intent (HealReact's own attr if user opted in)
  id: string | null;              // DOM id
  name: string | null;            // form name attribute
  placeholder: string | null;     // placeholder text
  text: string | null;            // static child text, if trivially extractable
  i18nKey: string | null;         // t('key') or i18n.t('key') reference
  className: string | null;       // raw className string (often dynamic; logged anyway)
  href: string | null;            // for <a>
  hasOnClick: boolean;
  hasOnChange: boolean;
  hasOnSubmit: boolean;
  parentChain: string[];          // enclosing JSX element tags, outer → inner
  // Custom data-* attributes other than data-testid / data-test-id / data-test /
  // data-intent (which already have dedicated fields). Critical for projects
  // that use their own data-* convention as the stable anchor (e.g. koenig
  // uses data-kg-card, data-kg-card-toolbar, data-kg-canvas, etc.).
  // Stored as { 'data-kg-card-toolbar': 'html', ... }; value may be the raw
  // expression text if it's a JS expression, just like getAttr() returns.
  dataAttrs: Record<string, string>;
  // Filled later by intent_labeller.ts:
  intent: string | null;
}

const INTERACTIVE_TAGS = new Set([
  "button", "a", "input", "select", "textarea", "form", "label",
  // Common library aliases — we keep them; the labeller can reason about them
  "Button", "Link", "Input", "Select", "TextField", "Form", "IconButton", "MenuItem", "Tab",
]);

// Implicit ARIA roles for native HTML elements we care about.
const IMPLICIT_ROLE: Record<string, string> = {
  button: "button",
  a: "link",
  input: "textbox",           // refined below for input[type=...]
  select: "combobox",
  textarea: "textbox",
  form: "form",
  label: "label",
};

function getAttr(el: JsxOpeningElement | JsxSelfClosingElement, name: string): string | null {
  const attr = el.getAttribute(name);
  if (!attr) return null;
  if (attr.getKind() !== SyntaxKind.JsxAttribute) return null;
  const init = (attr as any).getInitializer?.();
  if (!init) return ""; // bare attr like <input disabled />
  if (init.getKind() === SyntaxKind.StringLiteral) {
    return init.getLiteralText();
  }
  // JsxExpression — return the raw source text so the labeller can reason about it
  const text = init.getText();
  return text.length > 200 ? text.slice(0, 200) + "…" : text;
}

function inferRole(tag: string, el: JsxOpeningElement | JsxSelfClosingElement): string | null {
  const explicit = getAttr(el, "role");
  if (explicit) return explicit.replace(/['"{}]/g, "");
  const base = IMPLICIT_ROLE[tag];
  if (!base) return null;
  if (tag === "input") {
    const type = (getAttr(el, "type") ?? "text").replace(/['"{}]/g, "");
    if (type === "button" || type === "submit" || type === "reset") return "button";
    if (type === "checkbox") return "checkbox";
    if (type === "radio") return "radio";
    if (type === "range") return "slider";
    if (type === "search") return "searchbox";
    return "textbox";
  }
  return base;
}

function extractI18nKey(raw: string | null): string | null {
  if (!raw) return null;
  // Match t('foo.bar') / i18n.t("foo") / useTranslation -> t('foo')
  const m = raw.match(/(?:^|\b)(?:i18n\.)?t\(\s*['"`]([^'"`]+)['"`]\s*[),]/);
  return m ? m[1] : null;
}

function extractStaticText(el: JsxOpeningElement | JsxSelfClosingElement): string | null {
  if (el.getKind() === SyntaxKind.JsxSelfClosingElement) return null;
  const parent = el.getParent();
  if (!parent || parent.getKind() !== SyntaxKind.JsxElement) return null;
  const children = (parent as any).getJsxChildren?.() ?? [];
  for (const c of children) {
    if (c.getKind() === SyntaxKind.JsxText) {
      const t = c.getText().trim();
      if (t) return t.length > 80 ? t.slice(0, 80) + "…" : t;
    }
  }
  return null;
}

function enclosingComponentName(node: Node): string | null {
  let cur: Node | undefined = node;
  while (cur) {
    if (cur.getKind() === SyntaxKind.FunctionDeclaration) {
      const name = (cur as any).getName?.();
      if (name && /^[A-Z]/.test(name)) return name;
    }
    if (cur.getKind() === SyntaxKind.VariableDeclaration) {
      const name = (cur as any).getName?.();
      if (name && /^[A-Z]/.test(name)) return name;
    }
    if (cur.getKind() === SyntaxKind.ClassDeclaration) {
      const name = (cur as any).getName?.();
      if (name) return name;
    }
    cur = cur.getParent();
  }
  return null;
}

function parentChain(node: Node, maxDepth = 5): string[] {
  const chain: string[] = [];
  let cur: Node | undefined = node.getParent();
  let depth = 0;
  while (cur && depth < maxDepth) {
    if (cur.getKind() === SyntaxKind.JsxElement) {
      const opening = (cur as any).getOpeningElement?.();
      if (opening) chain.unshift(opening.getTagNameNode().getText());
    }
    cur = cur.getParent();
    depth++;
  }
  return chain;
}

function isInteractive(tag: string, el: JsxOpeningElement | JsxSelfClosingElement): boolean {
  if (INTERACTIVE_TAGS.has(tag)) return true;
  // Anything with explicit role={button|link|...} counts.
  const role = getAttr(el, "role");
  if (role && /(button|link|menuitem|tab|checkbox|radio|switch|combobox|textbox|searchbox)/i.test(role)) return true;
  // Anything with onClick / onChange / onSubmit handler counts.
  for (const h of ["onClick", "onChange", "onSubmit"]) {
    if (el.getAttribute(h)) return true;
  }
  // Anchor-bearing custom components: any element that exposes a stable anchor
  // (data-testid, data-kg-*, data-test, data-cy, aria-label, role) is worth
  // recording even if it isn't itself a clickable control. Real React projects
  // routinely place these anchors on wrapper components (Toolbar, CardMenu,
  // Modal) that Playwright tests then descend into.
  for (const a of el.getAttributes()) {
    if (a.getKind() !== SyntaxKind.JsxAttribute) continue;
    const n = (a as any).getNameNode?.()?.getText?.();
    if (typeof n !== "string") continue;
    if (n === "data-testid" || n === "data-test-id" || n === "data-test" || n === "data-cy") return true;
    if (n === "dataTestId" || n === "testId" || n === "testID") return true;
    if (n === "aria-label" || n === "aria-labelledby") return true;
    if (n.startsWith("data-kg-")) return true;
  }
  return false;
}

interface ExtractOptions {
  srcRoot: string;
  outPath: string;
}

export function extract(opts: ExtractOptions): LocatorRecord[] {
  const project = new Project({
    skipAddingFilesFromTsConfig: true,
    compilerOptions: { allowJs: true, jsx: 4 /* ReactJSX */ },
  });
  project.addSourceFilesAtPaths([
    `${opts.srcRoot}/**/*.tsx`,
    `${opts.srcRoot}/**/*.jsx`,
    `${opts.srcRoot}/**/*.ts`,
    `${opts.srcRoot}/**/*.js`,
    `!${opts.srcRoot}/**/node_modules/**`,
    `!${opts.srcRoot}/**/*.test.*`,
    `!${opts.srcRoot}/**/*.spec.*`,
  ]);

  const records: LocatorRecord[] = [];
  for (const sf of project.getSourceFiles()) {
    const relPath = relative(process.cwd(), sf.getFilePath());
    sf.forEachDescendant((node) => {
      const kind = node.getKind();
      if (kind !== SyntaxKind.JsxOpeningElement && kind !== SyntaxKind.JsxSelfClosingElement) return;
      const el = node as JsxOpeningElement | JsxSelfClosingElement;
      const tag = el.getTagNameNode().getText();
      if (!isInteractive(tag, el)) return;

      // Collect custom data-* attributes (not data-testid / data-test* / data-intent).
      const dataAttrs: Record<string, string> = {};
      const RESERVED = new Set(["data-testid", "data-test-id", "data-test", "data-intent"]);
      for (const a of el.getAttributes()) {
        if (a.getKind() !== SyntaxKind.JsxAttribute) continue;
        const name = (a as any).getNameNode?.()?.getText?.();
        if (typeof name !== "string" || !name.startsWith("data-")) continue;
        if (RESERVED.has(name)) continue;
        const v = getAttr(el, name);
        if (v !== null) dataAttrs[name] = v;
      }
      const className = getAttr(el, "className");
      const ariaLabelRaw = getAttr(el, "aria-label") ?? getAttr(el, "aria-labelledby");
      const ariaLabel = ariaLabelRaw;
      const i18nFromAria = extractI18nKey(ariaLabelRaw);
      const placeholderRaw = getAttr(el, "placeholder");
      const i18nFromPlaceholder = extractI18nKey(placeholderRaw);
      const textChild = extractStaticText(el);
      const i18nFromChild = extractI18nKey(textChild);

      const pos = sf.getLineAndColumnAtPos(node.getStart());

      records.push({
        componentFile: relPath,
        componentName: enclosingComponentName(node),
        elementTag: tag,
        line: pos.line,
        column: pos.column,
        role: inferRole(tag, el),
        ariaLabel,
        // Real React projects routinely route testids through camelCase props
        // (e.g. <MediaPlaceholder dataTestId="x" />). Treat those as testId so
        // the resolver can still match the rendered selector at runtime.
        testId: getAttr(el, "data-testid") ?? getAttr(el, "data-test-id") ?? getAttr(el, "data-test")
                ?? getAttr(el, "dataTestId") ?? getAttr(el, "testId") ?? getAttr(el, "testID"),
        dataIntent: getAttr(el, "data-intent"),
        id: getAttr(el, "id"),
        name: getAttr(el, "name"),
        placeholder: placeholderRaw,
        text: textChild,
        i18nKey: i18nFromAria ?? i18nFromPlaceholder ?? i18nFromChild,
        className,
        href: getAttr(el, "href"),
        hasOnClick: !!el.getAttribute("onClick"),
        hasOnChange: !!el.getAttribute("onChange"),
        hasOnSubmit: !!el.getAttribute("onSubmit"),
        parentChain: parentChain(node),
        dataAttrs,
        intent: null, // filled by intent_labeller.ts
      });
    });
  }

  if (!existsSync(dirname(opts.outPath))) mkdirSync(dirname(opts.outPath), { recursive: true });
  writeFileSync(opts.outPath, JSON.stringify({ generatedAt: new Date().toISOString(), srcRoot: opts.srcRoot, count: records.length, records }, null, 2));
  return records;
}

function parseArgs(argv: string[]): ExtractOptions {
  let src = "src";
  let out = "LocatorSheet.json";
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === "--src") src = argv[++i];
    else if (argv[i] === "--out") out = argv[++i];
  }
  return { srcRoot: resolve(src), outPath: resolve(out) };
}

const isMain = import.meta.url === `file://${process.argv[1]}`;
if (isMain) {
  const opts = parseArgs(process.argv.slice(2));
  const records = extract(opts);
  // eslint-disable-next-line no-console
  console.log(`✅ extracted ${records.length} interactive elements from ${opts.srcRoot}`);
  console.log(`   → ${opts.outPath}`);
  const byTag: Record<string, number> = {};
  for (const r of records) byTag[r.elementTag] = (byTag[r.elementTag] ?? 0) + 1;
  console.log("   by tag:", byTag);
}
