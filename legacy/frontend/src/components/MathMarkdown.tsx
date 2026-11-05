"use client";

import ReactMarkdown from "react-markdown";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import "katex/dist/katex.min.css";

type Props = {
  children: string;
  className?: string;
  /** Jasne kolory (np. zrzut na białym tle / schowek). */
  variant?: "dark" | "light";
  /**
   * Zrzut PNG (html-to-image): kolory tylko jako #hex / inline style — bez klas Tailwind z `lab()`,
   * które psują serializację SVG. KaTeX dziedziczy `color` z akapitów.
   */
  exportSnapshot?: boolean;
};

/**
 * Markdown + LaTeX ($...$, $$...$$) — wzory przez KaTeX.
 */
export function MathMarkdown({
  children,
  className = "",
  variant = "dark",
  exportSnapshot = false,
}: Props) {
  const light = variant === "light";
  const snap = exportSnapshot;

  return (
    <div
      className={`markdown-math text-[15px] leading-relaxed ${
        snap ? "markdown-math-snapshot" : light ? "text-slate-900" : "text-slate-200"
      } ${className}`}
      style={
        snap
          ? { color: "#0f172a", fontSize: 15, lineHeight: 1.625 }
          : undefined
      }
    >
      {snap ? (
        <style
          dangerouslySetInnerHTML={{
            __html: `
.markdown-math-snapshot .katex,
.markdown-math-snapshot .katex * {
  color: #0f172a !important;
}
.markdown-math-snapshot .katex-display { margin: 0.75rem 0; }
`,
          }}
        />
      ) : null}
      <ReactMarkdown
        remarkPlugins={[remarkMath]}
        rehypePlugins={[rehypeKatex]}
        components={{
          p: ({ children: c }) => (
            <p
              className={
                snap
                  ? "mb-3 last:mb-0"
                  : "mb-3 last:mb-0 text-slate-900 [&_.katex]:text-slate-900 dark:text-slate-100 dark:[&_.katex]:text-slate-100"
              }
              style={snap ? { color: "#0f172a" } : undefined}
            >
              {c}
            </p>
          ),
          h1: ({ children: c }) => (
            <h1
              className={
                snap
                  ? "mb-3 mt-6 text-2xl font-bold first:mt-0"
                  : light
                    ? "mb-3 mt-6 text-2xl font-bold text-slate-950 first:mt-0"
                    : "mb-3 mt-6 text-2xl font-bold text-white first:mt-0"
              }
              style={snap ? { color: "#020617" } : undefined}
            >
              {c}
            </h1>
          ),
          h2: ({ children: c }) => (
            <h2
              className={
                snap
                  ? "mb-2 mt-6 text-xl font-semibold"
                  : light
                    ? "mb-2 mt-6 text-xl font-semibold text-slate-900"
                    : "mb-2 mt-6 text-xl font-semibold text-slate-100"
              }
              style={snap ? { color: "#0f172a" } : undefined}
            >
              {c}
            </h2>
          ),
          h3: ({ children: c }) => (
            <h3
              className={
                snap
                  ? "mb-2 mt-4 text-lg font-semibold"
                  : light
                    ? "mb-2 mt-4 text-lg font-semibold text-slate-800"
                    : "mb-2 mt-4 text-lg font-semibold text-slate-200"
              }
              style={snap ? { color: "#1e293b" } : undefined}
            >
              {c}
            </h3>
          ),
          ul: ({ children: c }) => (
            <ul
              className={
                snap
                  ? "my-3 list-disc space-y-1 pl-6"
                  : light
                    ? "my-3 list-disc space-y-1 pl-6 text-slate-800"
                    : "my-3 list-disc space-y-1 pl-6 text-slate-300"
              }
              style={snap ? { color: "#1e293b" } : undefined}
            >
              {c}
            </ul>
          ),
          ol: ({ children: c }) => (
            <ol
              className={
                snap
                  ? "my-3 list-decimal space-y-1 pl-6"
                  : light
                    ? "my-3 list-decimal space-y-1 pl-6 text-slate-800"
                    : "my-3 list-decimal space-y-1 pl-6 text-slate-300"
              }
              style={snap ? { color: "#1e293b" } : undefined}
            >
              {c}
            </ol>
          ),
          li: ({ children: c }) => (
            <li className="leading-relaxed">{c}</li>
          ),
          code: ({ className: codeClass, children: c, ...props }) => {
            const isBlock = String(codeClass).includes("language-");
            if (isBlock) {
              return (
                <code
                  className={
                    snap
                      ? "block overflow-x-auto rounded-lg border p-3 text-sm"
                      : light
                        ? "block overflow-x-auto rounded-lg border border-slate-200 bg-slate-100 p-3 text-sm text-slate-900"
                        : "block overflow-x-auto rounded-lg border border-white/10 bg-slate-950/90 p-3 text-sm text-cyan-100"
                  }
                  style={
                    snap
                      ? {
                          border: "1px solid #e2e8f0",
                          backgroundColor: "#f1f5f9",
                          color: "#0f172a",
                        }
                      : undefined
                  }
                  {...props}
                >
                  {c}
                </code>
              );
            }
            return (
              <code
                className={
                  snap
                    ? "rounded-md px-1.5 py-0.5 text-sm"
                    : light
                      ? "rounded-md bg-slate-200 px-1.5 py-0.5 text-sm text-slate-900"
                      : "rounded-md bg-slate-950 px-1.5 py-0.5 text-sm text-cyan-200"
                }
                style={
                  snap
                    ? {
                        backgroundColor: "#e2e8f0",
                        color: "#0f172a",
                      }
                    : undefined
                }
                {...props}
              >
                {c}
              </code>
            );
          },
          pre: ({ children: c }) => (
            <pre
              className={
                snap
                  ? "my-4 overflow-x-auto rounded-xl border p-4"
                  : light
                    ? "my-4 overflow-x-auto rounded-xl border border-slate-200 bg-slate-100 p-4"
                    : "my-4 overflow-x-auto rounded-xl border border-white/10 bg-slate-950/80 p-4"
              }
              style={
                snap
                  ? {
                      border: "1px solid #e2e8f0",
                      backgroundColor: "#f1f5f9",
                    }
                  : undefined
              }
            >
              {c}
            </pre>
          ),
          strong: ({ children: c }) => (
            <strong
              className={
                snap
                  ? "font-semibold"
                  : light
                    ? "font-semibold text-slate-950"
                    : "font-semibold text-white"
              }
              style={snap ? { color: "#020617" } : undefined}
            >
              {c}
            </strong>
          ),
        }}
      >
        {children}
      </ReactMarkdown>
    </div>
  );
}
