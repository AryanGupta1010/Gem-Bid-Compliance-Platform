export type Status = "PASS" | "FAIL" | "REVIEW" | "UNAVAILABLE";
export type Risk = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

export interface DocumentRecord {
  id: string; filename: string; status: string;
  mime_type?: string | null; size_bytes?: number | null;
  hash_sha3_512?: string | null; minio_path?: string | null;
  processing_stage?: string | null; page_count?: number | null;
}
interface RuleResult {
  id: string; rule_id: string; rule_name: string; result: Status;
  description?: string | null; extracted_value?: string | null;
  expected_value?: string | null; confidence?: number | null;
  evidence?: string | null; document_name?: string | null;
  document_id?: string | null; page?: number | null;
  bounding_box?: number[] | null; source?: string | null;
  timestamp?: string | null; model_version?: string | null; rule_version?: string | null;
}
export interface Bidder {
  id: string; tender_id: string; bidder_name: string; gstin?: string | null;
  score: number; risk: Risk; status: Status; failed_rules: number; review_rules: number;
  summary?: string | null; reviewer_decision?: string | null;
  reviewer_note?: string | null; reviewed_at?: string | null;
  documents: DocumentRecord[]; rules: RuleResult[];
}
export interface Tender {
  id: string; title: string; department: string; published: string;
  deadline: string; budget: string; status: string; bids: Bidder[];
}
export type TenderCreate = Pick<Tender, "title" | "department" | "deadline" | "budget">;
export interface AuditEvent {
  id: string; time: string; actor: string; action: string;
  document?: string | null; rule?: string | null; result?: string | null;
  source?: string | null; hash?: string | null;
}
export interface BidStatus {
  bid_id: string; bid_status: Status; bid_risk: Risk; bid_score: number;
  documents: { document_id: string; filename: string; status: string; processing_stage: string; page_count: number }[];
  rules_count: number; reviewer_decision?: string | null;
}
export interface Capabilities {
  ai_mode: string; retrieval: string; extraction: string;
  connectors: { name: string; mode: string }[];
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  username: string;
  role: string;
  full_name: string;
}

export interface LoginCredentials {
  username: string;
  password: string;
}
