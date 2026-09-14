import type { AuditEvent, Bidder, BidStatus, Capabilities, DocumentRecord, Tender, TenderCreate } from "./types";

class ApiError extends Error {
  constructor(message: string, public status: number) { super(message); }
}
const base = () => typeof window === "undefined"
  ? (process.env.API_BASE_URL || "http://127.0.0.1:8000").replace(/\/$/, "")
  : "/api";
export const apiUrl = (path: string) => `${base()}${path}`;
async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 60000);
  try {
    const response = await fetch(apiUrl(path), { ...init, cache: "no-store", signal: controller.signal });
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
    throw new Error("The backend is unavailable or the request timed out. Check services and retry.");
  } finally { clearTimeout(timer); }
}
const json = (body: unknown): RequestInit => ({ method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
async function optional<T>(path: string): Promise<T | null> {
  try { return await request<T>(path); }
  catch (error) { if (error instanceof ApiError && error.status === 404) return null; throw error; }
}
export const services = {
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
