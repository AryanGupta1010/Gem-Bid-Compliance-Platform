import { AppShell } from "@/components/app-shell";
import { PageHeader } from "@/components/ui";
import { SettingsClient } from "@/components/settings-client";

export default function SettingsPage() {
  return (
    <AppShell>
      <PageHeader
        eyebrow="Workspace administration"
        title="Settings"
        description="Configure the verification workspace without changing the human-control boundary."
      />

      <SettingsClient />
    </AppShell>
  );
}
