import { AppShell } from "@/components/layout/app-shell";
import { SettingsClient } from "@/components/settings/settings-client";
import { services } from "@/lib/services";
export default async function VerificationPage() {
  const capabilities = await services.getCapabilities();
  return <AppShell><h1 className="page-title mb-3">Verification sources</h1><p className="mb-5 muted">These are implementation modes, not live connectivity checks. Inspect the bidder rules for recorded verification evidence.</p><SettingsClient capabilities={capabilities}/></AppShell>;
}
