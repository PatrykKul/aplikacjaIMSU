import { Badge } from "@/shared/ui/badge";

export function PublicationBadge({ isPublished }: { isPublished: boolean }) {
  return isPublished ? (
    <Badge>Opublikowany</Badge>
  ) : (
    <Badge variant="outline">Prywatny</Badge>
  );
}
