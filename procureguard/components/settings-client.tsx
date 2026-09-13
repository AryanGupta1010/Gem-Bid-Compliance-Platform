"use client";

import { useEffect, useState } from "react";
import { Bell, Database, LockKeyhole, Settings2, ShieldCheck, Save } from "lucide-react";

export function SettingsClient() {
  const [demoMode, setDemoMode] = useState(true);
  const [notificationsEnabled, setNotificationsEnabled] = useState(true);
  const [isSaved, setIsSaved] = useState(false);

  useEffect(() => {
    const savedDemoMode = localStorage.getItem("demoMode");
    const savedNotifications = localStorage.getItem("notificationsEnabled");
    
    if (savedDemoMode !== null) {
      setDemoMode(savedDemoMode === "true");
    }
    if (savedNotifications !== null) {
      setNotificationsEnabled(savedNotifications === "true");
    }
  }, []);

  const handleSave = () => {
    localStorage.setItem("demoMode", demoMode.toString());
    localStorage.setItem("notificationsEnabled", notificationsEnabled.toString());
    setIsSaved(true);
    setTimeout(() => setIsSaved(false), 2000);
  };

  const settings = [
    {
      title: "Verification connectors",
      description: "Manage live sandbox and adapter-backed verification sources.",
      icon: Database,
      status: "GST sandbox connected"
    },
    {
      title: "Rule engine",
      description: "Review the active deterministic GeM rule version and thresholds.",
      icon: Settings2,
      status: "GeM-Ruleset 1.4.0"
    },
    {
      title: "Access control",
      description: "Configure procurement-officer roles, authentication and session policy.",
      icon: LockKeyhole,
      status: "Role-based access enabled"
    },
    {
      title: "Audit protection",
      description: "Document sealing, event retention and evidence lineage controls.",
      icon: ShieldCheck,
      status: "SHA-3-512 sealing enabled"
    }
  ];

  return (
    <>
      <div className="grid gap-4 lg:grid-cols-2">
        {settings.map(({ title, description, icon: Icon, status }) => (
          <div key={title} className="panel flex items-start gap-4 p-5 text-left transition hover:border-teal/40 hover:shadow-md">
            <div className="rounded-lg bg-cyan-50 p-2.5 text-teal">
              <Icon size={19} />
            </div>
            <div className="min-w-0 flex-1">
              <h2 className="font-semibold">{title}</h2>
              <p className="mt-1 text-sm leading-6 muted">{description}</p>
              <p className="mt-3 text-xs font-semibold text-teal">{status}</p>
            </div>
          </div>
        ))}
        
        {/* Interactive Settings */}
        <div className="panel flex items-start gap-4 p-5 text-left transition hover:border-teal/40 hover:shadow-md">
          <div className="rounded-lg bg-cyan-50 p-2.5 text-teal">
            <Bell size={19} />
          </div>
          <div className="min-w-0 flex-1">
            <h2 className="font-semibold flex items-center justify-between">
              Notifications
              <label className="relative inline-flex items-center cursor-pointer">
                <input 
                  type="checkbox" 
                  className="sr-only peer" 
                  checked={notificationsEnabled}
                  onChange={(e) => setNotificationsEnabled(e.target.checked)}
                />
                <div className="w-9 h-5 bg-slate-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-teal"></div>
              </label>
            </h2>
            <p className="mt-1 text-sm leading-6 muted">Choose when review items and connector failures appear in the queue.</p>
            <p className="mt-3 text-xs font-semibold text-teal">{notificationsEnabled ? "Officer alerts enabled" : "Officer alerts disabled"}</p>
          </div>
        </div>

        <div className="panel flex items-start gap-4 p-5 text-left transition hover:border-teal/40 hover:shadow-md">
          <div className="rounded-lg bg-amber-50 p-2.5 text-amber-600">
            <Settings2 size={19} />
          </div>
          <div className="min-w-0 flex-1">
            <h2 className="font-semibold flex items-center justify-between">
              Application Mode
              <label className="relative inline-flex items-center cursor-pointer">
                <input 
                  type="checkbox" 
                  className="sr-only peer" 
                  checked={demoMode}
                  onChange={(e) => setDemoMode(e.target.checked)}
                />
                <div className="w-9 h-5 bg-slate-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-amber-500"></div>
              </label>
            </h2>
            <p className="mt-1 text-sm leading-6 muted">Toggle between AI inference and deterministic demo fallbacks.</p>
            <p className="mt-3 text-xs font-semibold text-amber-600">{demoMode ? "Demo Mode (Mock DB) Active" : "Production Mode Active"}</p>
          </div>
        </div>
      </div>

      <div className="mt-6 flex justify-end">
        <button 
          onClick={handleSave}
          className="btn btn-primary flex items-center gap-2"
        >
          <Save size={16} />
          {isSaved ? "Saved!" : "Save Preferences"}
        </button>
      </div>

      <div className="mt-6 panel p-5">
        <p className="section-title">Governance policy</p>
        <h2 className="mt-1 text-lg font-semibold">Decision-support mode is enforced</h2>
        <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">
          ProcureGuard may locate evidence, verify identifiers and recommend an outcome. It cannot autonomously
          disqualify a bidder or submit a procurement decision.
        </p>
        <div className="mt-5 flex items-center gap-2 rounded-lg border border-emerald-100 bg-emerald-50 p-3 text-sm text-emerald-800">
          <ShieldCheck size={16} />
          Human approval is required for every final decision.
        </div>
      </div>
    </>
  );
}
