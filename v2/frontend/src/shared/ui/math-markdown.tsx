import "katex/dist/katex.min.css";

import Markdown, { type Components } from "react-markdown";
import rehypeKatex from "rehype-katex";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";

import { cn } from "@/shared/lib/utils";

const remarkPlugins = [remarkGfm, remarkMath];
const rehypePlugins = [rehypeKatex];

// Inline text (e.g. a choice option inside a <label>) may not contain <p>
const inlineComponents: Components = {
  p: ({ children }) => <>{children}</>,
};

type MathMarkdownProps = {
  children: string;
  className?: string;
  inline?: boolean;
};

// Markdown with TeX formulas ($...$ inline, $$...$$ as a block).
// Raw HTML in the text is not rendered, so lesson content cannot inject markup.
export function MathMarkdown({
  children,
  className,
  inline,
}: MathMarkdownProps) {
  const Wrapper = inline ? "span" : "div";
  return (
    <Wrapper className={cn("math-markdown", className)}>
      <Markdown
        remarkPlugins={remarkPlugins}
        rehypePlugins={rehypePlugins}
        components={inline ? inlineComponents : undefined}
      >
        {children}
      </Markdown>
    </Wrapper>
  );
}
