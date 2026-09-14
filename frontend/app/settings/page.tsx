import { AppShell } from "@/components/layout/app-shell";
import { SettingsClient } from "@/components/settings/settings-client";
import { services } from "@/lib/services";
export default async function SettingsPage() {
  const capabilities = await services.getCapabilities();
  return <AppShell><h1 className="page-title mb-5">Settings</h1><SettingsClient capabilities={capabilities}/></AppShell>;
}
