import { RoleGate } from "@/features/auth/components/RoleGate";
import { StudentClassroomsPage } from "@/features/classes/components/StudentClassroomsPage";

// Teachers manage their classrooms under /teach/classes
export default function ClassesPage() {
  return (
    <RoleGate roles={["student"]}>
      <StudentClassroomsPage />
    </RoleGate>
  );
}
