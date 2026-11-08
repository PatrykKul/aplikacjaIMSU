import { InlineMath } from "@tiptap/extension-mathematics";
import { TableKit } from "@tiptap/extension-table";
import { type Extensions, InputRule } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";

/**
 * Finds `$latex$` just typed at the end of `text` (TipTap's default is `$$latex$$`).
 * Like in Markdown, the formula may not start or end with a space, so prices
 * such as "5$ i 6$" stay text.
 */
export function findDollarMath(text: string) {
  const match = /\$([^$\n]+)\$$/.exec(text);
  if (!match) {
    return null;
  }
  const latex = match[1];
  if (/^\s|\s$/.test(latex) || text[match.index - 1] === "$") {
    return null;
  }
  return { index: match.index, text: match[0], data: { latex } };
}

const DollarInlineMath = InlineMath.extend({
  addInputRules() {
    return [
      new InputRule({
        find: findDollarMath,
        handler: ({ state, range, match }) => {
          const latex = match.data?.latex;
          if (typeof latex !== "string") {
            return null;
          }
          state.tr.replaceWith(
            range.from,
            range.to,
            this.type.create({ latex }),
          );
        },
      }),
    ];
  },
});

type ExtensionOptions = {
  /** Called when a formula is clicked in an editable document. */
  onMathClick?: (latex: string, pos: number) => void;
};

/**
 * One schema for editing and reading. No image node: images pasted from Word
 * are dropped, a picture is added as an attachment with its V / A / K forms.
 */
export function richTextExtensions({
  onMathClick,
}: ExtensionOptions = {}): Extensions {
  return [
    StarterKit.configure({
      heading: { levels: [2, 3] },
      blockquote: false,
      code: false,
      codeBlock: false,
      horizontalRule: false,
      strike: false,
      link: {
        openOnClick: false,
        autolink: true,
        defaultProtocol: "https",
        HTMLAttributes: { target: "_blank", rel: "noopener noreferrer" },
      },
    }),
    TableKit.configure({ table: { resizable: false } }),
    DollarInlineMath.configure({
      katexOptions: { throwOnError: false },
      onClick: onMathClick
        ? (node, pos) => onMathClick(node.attrs.latex as string, pos)
        : undefined,
    }),
  ];
}
