import { RoleGate } from "@/features/auth/components/RoleGate";
import { TeacherClassroomsPage } from "@/features/teach/components/TeacherClassroomsPage";

export default function TeachClassesPage() {
  return (
    <RoleGate roles={["teacher"]}>
      <TeacherClassroomsPage />
    </RoleGate>
  );
}
