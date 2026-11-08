import { RoleGate } from "@/features/auth/components/RoleGate";
import { TeacherCoursesPage } from "@/features/teach/components/TeacherCoursesPage";

export default function TeachPage() {
  return (
    <RoleGate roles={["teacher"]}>
      <TeacherCoursesPage />
    </RoleGate>
  );
}
