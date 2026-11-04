import "katex/dist/katex.min.css";

import Markdown from "react-markdown";
import rehypeKatex from "rehype-katex";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";

import { cn } from "@/shared/lib/utils";

const remarkPlugins = [remarkGfm, remarkMath];
const rehypePlugins = [rehypeKatex];

type MathMarkdownProps = { children: string; className?: string };

// Markdown with TeX formulas ($...$ inline, $$...$$ as a block).
// Raw HTML in the text is not rendered, so lesson content cannot inject markup.
export function MathMarkdown({ children, className }: MathMarkdownProps) {
  return (
    <div className={cn("math-markdown", className)}>
      <Markdown remarkPlugins={remarkPlugins} rehypePlugins={rehypePlugins}>
        {children}
      </Markdown>
    </div>
  );
}
