const API_BASE = process.env.NEXT_PUBLIC_API_URL 
  ? `${process.env.NEXT_PUBLIC_API_URL}/api` 
  : "http://localhost:8000/api";

export async function fetchApi<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const token = typeof window !== "undefined" ? localStorage.getItem("gem_token") : null;
  
  const headers: HeadersInit = {
    ...(options.headers || {}),
  };

  if (token) {
    (headers as Record<string, string>)["Authorization"] = `Bearer ${token}`;
  }

  if (!(options.body instanceof FormData)) {
    (headers as Record<string, string>)["Content-Type"] = "application/json";
  }

  const res = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  if (!res.ok) {
    let errMessage = `API Error: ${res.status} ${res.statusText}`;
    try {
      const errData = await res.json();
      errMessage = errData.message || errData.detail || errMessage;
    } catch {
      // ignore
    }
    throw new Error(errMessage);
  }

  return res.json();
}

export const api = {
  // Auth
  login: (data: { email: string; password: string }) => 
    fetchApi<any>("/auth/login", { method: "POST", body: JSON.stringify(data) }),
  getMe: () => fetchApi<any>("/auth/me"),

  // Tenders
  getTenders: () => fetchApi<any[]>("/tenders"),
  getTender: (id: string) => fetchApi<any>(`/tenders/${id}`),
  createTender: (data: any) => fetchApi<any>("/tenders", { method: "POST", body: JSON.stringify(data) }),
  createRequirement: (tenderId: string, data: any) => 
    fetchApi<any>(`/tenders/${tenderId}/requirements`, { method: "POST", body: JSON.stringify(data) }),
  createTenderVersion: (tenderId: string, summary: string) =>
    fetchApi<any>(`/tenders/${tenderId}/versions?change_summary=${encodeURIComponent(summary)}`, { method: "POST" }),

  // Bidders
  getBidders: () => fetchApi<any[]>("/bidders"),
  createBidder: (data: any) => fetchApi<any>("/bidders", { method: "POST", body: JSON.stringify(data) }),

  // Bids
  getBids: (tenderId?: string) => fetchApi<any[]>(tenderId ? `/bids?tender_id=${tenderId}` : "/bids"),
  getBid: (id: string) => fetchApi<any>(`/bids/${id}`),
  createBid: (data: any) => fetchApi<any>("/bids", { method: "POST", body: JSON.stringify(data) }),
  uploadDocument: (bidId: string, formData: FormData) => 
    fetchApi<any>(`/bids/${bidId}/documents`, { method: "POST", body: formData }),
  verifyBid: (bidId: string) => 
    fetchApi<any>(`/bids/${bidId}/verify`, { method: "POST" }),
  getBidRules: (bidId: string) => fetchApi<any[]>(`/bids/${bidId}/rules`),
  getBidAssessment: (bidId: string) => fetchApi<any>(`/bids/${bidId}/assessment`),
  getBidEvidence: (bidId: string) => fetchApi<any[]>(`/bids/${bidId}/evidence`),
  getBidAudit: (bidId: string) => fetchApi<any[]>(`/bids/${bidId}/audit`),

  // Review
  submitReview: (bidId: string, data: { decision: string; officer_notes: string }) =>
    fetchApi<any>(`/bids/${bidId}/review`, { method: "POST", body: JSON.stringify(data) }),
  getReviews: (bidId: string) => fetchApi<any[]>(`/bids/${bidId}/review`),

  // Audit
  getAllAudit: (limit = 100) => fetchApi<any[]>(`/audit?limit=${limit}`),

  // Verification
  queryVerification: (source: string, identifier: string) =>
    fetchApi<any>("/verification/query", {
      method: "POST",
      body: JSON.stringify({ source, identifier }),
    }),
};
