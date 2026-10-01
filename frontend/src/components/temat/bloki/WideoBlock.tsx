import { mediaSrc } from "@/lib/api";

/** Keeps only the <iframe> from pasted embed code and drops inline JS handlers. */
export function sanitizeVideoEmbedHtml(html: string): string {
  const withoutScripts = html.replace(/<script[\s\S]*?>[\s\S]*?<\/script>/gi, "");
  const iframeMatch = withoutScripts.match(/<iframe[\s\S]*?<\/iframe>/i);
  if (!iframeMatch) return "";
  return iframeMatch[0].replace(/\son\w+="[^"]*"/gi, "");
}

/** YouTube watch / short link -> embed URL; null when the text is not a YouTube link. */
function youtubeEmbedUrl(tekst: string): string | null {
  const m = tekst.match(
    /^https?:\/\/(?:www\.)?(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([\w-]{6,})/i
  );
  return m ? `https://www.youtube-nocookie.com/embed/${m[1]}` : null;
}

type Props = { tresc: string; onPlay?: () => void };

/** Wideo: kod iframe, link do YouTube albo adres pliku wideo. */
export function WideoBlock({ tresc, onPlay }: Props) {
  const tekst = tresc.trim();
  const frame =
    "relative aspect-video w-full max-w-full overflow-hidden rounded-2xl bg-black/30 shadow-[0_0_32px_rgba(0,0,0,0.25)] [&_iframe]:absolute [&_iframe]:inset-0 [&_iframe]:h-full [&_iframe]:w-full [&_iframe]:max-w-full [&_iframe]:border-0";

  const yt = youtubeEmbedUrl(tekst);
  if (yt) {
    return (
      <div className={frame}>
        <iframe
          src={yt}
          title="Wideo"
          allow="accelerometer; encrypted-media; picture-in-picture"
          allowFullScreen
        />
      </div>
    );
  }

  if (/^(https?:\/\/|\/)\S+\.(mp4|webm|ogv)(\?\S*)?$/i.test(tekst)) {
    return (
      <div className={frame}>
        {/* eslint-disable-next-line jsx-a11y/media-has-caption */}
        <video controls src={mediaSrc(tekst)} className="h-full w-full" onPlay={() => onPlay?.()} />
      </div>
    );
  }

  const embed = sanitizeVideoEmbedHtml(tekst);
  if (!embed) {
    return (
      <p className="rounded-xl border border-dashed border-slate-300 p-6 text-center text-sm text-slate-500 dark:border-slate-700">
        Brak wideo — wklej link do YouTube, adres pliku .mp4 albo kod osadzenia (iframe).
      </p>
    );
  }
  return <div className={frame} dangerouslySetInnerHTML={{ __html: embed }} />;
}
