import { notFound } from "next/navigation";

import { RoleGate } from "@/features/auth/components/RoleGate";
import { ClassroomEditor } from "@/features/teach/components/ClassroomEditor";

export default async function TeachClassroomPage(
  props: PageProps<"/teach/classes/[classroomId]">,
) {
  const { classroomId } = await props.params;
  const id = Number(classroomId);
  if (!Number.isSafeInteger(id) || id <= 0) {
    notFound();
  }
  return (
    <RoleGate roles={["teacher"]}>
      <ClassroomEditor classroomId={id} />
    </RoleGate>
  );
}
