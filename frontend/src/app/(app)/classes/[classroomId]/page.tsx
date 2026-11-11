import { notFound } from "next/navigation";

import { RoleGate } from "@/features/auth/components/RoleGate";
import { StudentClassroomView } from "@/features/classes/components/StudentClassroomView";

export default async function ClassroomPage(
  props: PageProps<"/classes/[classroomId]">,
) {
  const { classroomId } = await props.params;
  const id = Number(classroomId);
  if (!Number.isSafeInteger(id) || id <= 0) {
    notFound();
  }
  return (
    <RoleGate roles={["student"]}>
      <StudentClassroomView classroomId={id} />
    </RoleGate>
  );
}
