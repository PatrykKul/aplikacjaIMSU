import { HealthStatus } from "@/features/health/components/HealthStatus";

export default function HomePage() {
  return (
    <main className="mx-auto max-w-xl p-8">
      <h1 className="mb-4 text-2xl font-semibold">IMSU v2</h1>
      <HealthStatus />
    </main>
  );
}