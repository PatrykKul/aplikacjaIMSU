import { notFound } from "next/navigation";

import { ShellPreview } from "./ShellPreview";

export default function DevShellPage() {
  if (process.env.NODE_ENV === "production") {
    notFound();
  }
  return <ShellPreview />;
}
