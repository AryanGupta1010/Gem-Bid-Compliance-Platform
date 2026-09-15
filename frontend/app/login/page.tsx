"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Cookies from "js-cookie";
import { services } from "@/lib/services";

export default function LoginPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleEnterPlatform = async () => {
    setError("");
    setLoading(true);
    try {
      // Direct instant login without manual credentials
      const response = await services.login({ username: "admin", password: "password123" }).catch(async () => {
        // Fallback to secondary seeded admin if needed
        return await services.login({ username: "admin", password: "admin" }).catch(async () => {
          return await services.login({ username: "officer1", password: "ProcureGuard@2026" });
        });
      });

      Cookies.set("token", response.access_token, { expires: 1, path: "/" });
      Cookies.set("role", response.role || "ADMIN", { expires: 1, path: "/" });
      Cookies.set("username", response.username || "admin", { expires: 1, path: "/" });

      router.push("/");
      router.refresh();
    } catch (err: any) {
      // In case backend is temporarily unreachable, create a demo session token
      Cookies.set("token", "demo-session-token", { expires: 1, path: "/" });
      Cookies.set("role", "ADMIN", { expires: 1, path: "/" });
      Cookies.set("username", "admin", { expires: 1, path: "/" });
      router.push("/");
      router.refresh();
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-slate-900 via-slate-800 to-teal-950 px-4">
      <div className="w-full max-w-md space-y-8 rounded-2xl bg-white/95 backdrop-blur-md p-8 shadow-2xl ring-1 ring-white/20 text-center">
        <div className="space-y-3">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-teal-600 text-white shadow-lg shadow-teal-500/30 text-3xl font-bold">
            🛡️
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight text-gray-900">
            ProcureGuard
          </h1>
          <p className="text-sm font-medium text-teal-700 bg-teal-50 py-1 px-3 rounded-full inline-block border border-teal-200">
            AI-Powered Bid Compliance Platform
          </p>
          <p className="text-sm text-gray-600 pt-1">
            Smart India Hackathon Prototype &bull; Multi-Vector Audit System
          </p>
        </div>

        {error && (
          <div className="rounded-lg bg-red-50 p-3 text-sm text-red-700 border border-red-200">
            {error}
          </div>
        )}

        <div className="pt-4 space-y-4">
          <button
            type="button"
            onClick={handleEnterPlatform}
            disabled={loading}
            className="w-full group relative flex items-center justify-center gap-3 rounded-xl bg-gradient-to-r from-teal-600 to-emerald-600 px-6 py-4 text-base font-semibold text-white shadow-lg shadow-teal-600/30 hover:from-teal-500 hover:to-emerald-500 active:scale-[0.98] transition-all duration-150 disabled:opacity-50 cursor-pointer"
          >
            <span className="text-xl">🚀</span>
            <span>{loading ? "Entering Platform..." : "Enter Demo Platform"}</span>
            <span className="transition-transform group-hover:translate-x-1">&rarr;</span>
          </button>

          <p className="text-xs text-gray-500">
            Instant Demo Access Enabled &bull; No credentials required
          </p>
        </div>

        <div className="border-t border-gray-100 pt-4 flex justify-center items-center gap-4 text-xs text-gray-400">
          <span>ColPali Engine</span>
          <span>&bull;</span>
          <span>Surya OCR</span>
          <span>&bull;</span>
          <span>SaulLM Legal</span>
          <span>&bull;</span>
          <span>DeBERTa NLI</span>
        </div>
      </div>
    </div>
  );
}
