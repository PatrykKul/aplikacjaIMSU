import { RoleGate } from "@/features/auth/components/RoleGate";
import { CourseList } from "@/features/courses/components/CourseList";

// Teachers see their own courses under /teach (decision E7)
export default function CoursesPage() {
  return (
    <RoleGate roles={["student", "admin"]}>
      <CourseList />
    </RoleGate>
  );
}
