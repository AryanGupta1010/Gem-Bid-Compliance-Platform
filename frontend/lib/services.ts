import type { AuditEvent, Bidder, BidStatus, Capabilities, DocumentRecord, Tender, TenderCreate, AuthResponse, LoginCredentials } from "./types";

class ApiError extends Error {
  constructor(message: string, public status: number) { super(message); }
}
const base = () => {
  if (typeof window === "undefined") {
    return (process.env.API_BASE_URL || "http://backend:8000").replace(/\/$/, "");
  }
  return "/api";
};

export const apiUrl = (path: string) => `${base()}${path}`;

const getToken = () => {
  if (typeof window !== "undefined") {
    const m = document.cookie.match(/(^| )token=([^;]+)/);
    return m ? m[2] : null;
  }
  try {
    const { cookies } = require("next/headers");
    return cookies().get("token")?.value || null;
  } catch (e) {
    return null;
  }
};

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 60000);
  
  const headers = new Headers(init.headers || {});
  const token = getToken();
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  try {
    let response = await fetch(apiUrl(path), { ...init, headers, cache: "no-store", signal: controller.signal });
    
    // In browser, if /api rewrite returns 500/502/failed, attempt direct connection to localhost:8000
    if (!response.ok && typeof window !== "undefined" && (response.status === 500 || response.status === 502 || response.status === 504)) {
      try {
        const directResp = await fetch(`http://localhost:8000${path}`, { ...init, headers, cache: "no-store", signal: controller.signal });
        if (directResp.ok) {
          return await directResp.json() as T;
        }
      } catch (directErr) {
        // Continue with original response error
      }
    }

    if (!response.ok) {
      const body = await response.json().catch(() => null);
      const detail = body?.detail;
      const message = typeof detail === "string" ? detail : Array.isArray(detail)
        ? detail.map((item: { msg?: string }) => item.msg || "Invalid input").join("; ")
        : `Request failed (${response.status}). Please retry.`;
      throw new ApiError(message, response.status);
    }
    return await response.json() as T;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    throw new Error((error as any)?.message || "The backend is unavailable or the request timed out. Check services and retry.");
  } finally { clearTimeout(timer); }
}
const json = (body: unknown): RequestInit => ({ method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
async function optional<T>(path: string): Promise<T | null> {
  try { return await request<T>(path); }
  catch (error) { if (error instanceof ApiError && error.status === 404) return null; throw error; }
}
export const services = {
  login: (credentials: LoginCredentials) => request<AuthResponse>("/auth/login", json(credentials)),
  getAllTenders: () => request<Tender[]>("/tenders"),
  getTender: (id: string) => optional<Tender>(`/tenders/${encodeURIComponent(id)}`),
  createTender: (data: TenderCreate) => request<Tender>("/tenders", json(data)),
  createBid: (tenderId: string, bidder_name: string, gstin: string) => request<Bidder>("/bids", json({ tender_id: tenderId, bidder_name, gstin: gstin || null })),
  getAllBids: () => request<Bidder[]>("/bids"),
  getBid: (id: string) => optional<Bidder>(`/bids/${encodeURIComponent(id)}`),
  getBidStatus: (id: string) => request<BidStatus>(`/bids/${encodeURIComponent(id)}/status`),
  getAuditTrail: (bidId?: string) => request<AuditEvent[]>(`/audit${bidId ? `?bid_id=${encodeURIComponent(bidId)}` : ""}`),
  getCapabilities: () => request<Capabilities>("/capabilities"),
  recordDecision: (id: string, decision: string, note: string) => request<{ decision: string }>(`/bids/${encodeURIComponent(id)}/decision`, json({ decision, note })),
  uploadDocument: async (id: string, file: File) => {
    if (!file.name.toLowerCase().endsWith(".pdf") || file.size === 0 || file.size > 50 * 1024 * 1024) {
      throw new Error("Select a non-empty PDF no larger than 50 MB.");
    }
    const body = new FormData(); body.append("file", file);
    return request<DocumentRecord>(`/upload/${encodeURIComponent(id)}`, { method: "POST", body });
  },
};
