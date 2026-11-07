"use client";

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/shared/ui/tabs";

import { UsersTable } from "./UsersTable";

export function UsersPage() {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold tracking-tight">Użytkownicy</h1>
      <Tabs defaultValue="teacher" className="gap-6">
        <TabsList>
          <TabsTrigger value="teacher">Nauczyciele</TabsTrigger>
          <TabsTrigger value="student">Uczniowie</TabsTrigger>
        </TabsList>
        <TabsContent value="teacher">
          <UsersTable role="teacher" />
        </TabsContent>
        <TabsContent value="student">
          <UsersTable role="student" />
        </TabsContent>
      </Tabs>
    </div>
  );
}
