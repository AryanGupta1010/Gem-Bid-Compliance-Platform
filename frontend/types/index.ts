export type UserRole = "PROCUREMENT_OFFICER" | "ADMIN" | "AUDITOR";

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  department?: string;
  is_active: boolean;
}

export type TenderStatus = "DRAFT" | "ACTIVE" | "UNDER_EVALUATION" | "COMPLETED" | "ARCHIVED";

export type RuleType = 
  | "NUMERIC"
  | "DATE"
  | "BOOLEAN"
  | "STATUS"
  | "TEXT_MATCH"
  | "DOCUMENT_PRESENT"
  | "DOCUMENT_EXPIRY"
  | "VERIFICATION"
  | "MANUAL_REVIEW";

export type Operator = 
  | "EQ" | "NEQ" | "GT" | "GTE" | "LT" | "LTE" 
  | "EXISTS" | "NOT_EXISTS" | "IN" | "NOT_IN" 
  | "BEFORE" | "AFTER" | "CONTAINS";

export type Severity = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

export type RuleStatus = "PASS" | "FAIL" | "REVIEW" | "UNAVAILABLE";

export type RiskLevel = "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";

export type VerificationStatus = "VALID" | "INVALID" | "EXPIRED" | "NOT_FOUND" | "UNAVAILABLE";

export type OfficerDecisionType = "APPROVED" | "REJECTED" | "NEEDS_REVIEW";

export interface Requirement {
  id: string;
  tender_id: string;
  name: string;
  description?: string;
  rule_type: RuleType;
  operator: Operator;
  expected_value: string;
  unit?: string;
  evidence_type?: string;
  severity: Severity;
  mandatory: boolean;
  enabled: boolean;
  weight: number;
  exception_logic?: string;
  display_order: number;
  created_at: string;
}

export interface TenderVersion {
  id: string;
  tender_id: string;
  version_number: number;
  change_summary?: string;
  created_at: string;
}

export interface Tender {
  id: string;
  tender_number: string;
  title: string;
  description?: string;
  procuring_organization: string;
  status: TenderStatus;
  estimated_value?: number;
  currency: string;
  created_at: string;
  updated_at: string;
  requirements_count?: number;
  bids_count?: number;
  versions?: TenderVersion[];
  requirements?: Requirement[];
}

export interface Bidder {
  id: string;
  name: string;
  registration_number: string;
  gstin?: string;
  pan?: string;
  udyam_number?: string;
  contact_email: string;
  contact_phone?: string;
  is_msme: boolean;
  created_at: string;
}

export interface Evidence {
  id: string;
  document_id?: string;
  rule_result_id?: string;
  page_number: number;
  bounding_box?: number[]; // [x1, y1, x2, y2]
  extracted_field: string;
  extracted_value: string;
  confidence: number;
  source?: string;
  created_at: string;
}

export interface Document {
  id: string;
  bid_id: string;
  document_type: string;
  filename: string;
  file_path: string;
  mime_type: string;
  file_size: number;
  document_hash: string;
  page_count: number;
  metadata_json?: Record<string, any>;
  uploaded_at: string;
  evidences?: Evidence[];
}

export interface VerificationResult {
  id: string;
  source: string;
  request_identifier: string;
  status: VerificationStatus;
  response_data?: Record<string, any>;
  verified_at: string;
  adapter_version: string;
  success: boolean;
  error_code?: string;
  error_message?: string;
}

export interface RuleResult {
  id: string;
  bid_id: string;
  requirement_id: string;
  requirement_name?: string;
  rule_type?: RuleType;
  operator?: Operator;
  status: RuleStatus;
  actual_value?: string;
  expected_value?: string;
  unit?: string;
  explanation: string;
  severity: Severity;
  weight: number;
  confidence: number;
  rule_version: string;
  evaluated_at: string;
  evidences: Evidence[];
  verification_result?: VerificationResult;
}

export interface ComplianceAssessment {
  id: string;
  bid_id: string;
  compliance_score: number;
  risk_level: RiskLevel;
  recommendation: RuleStatus;
  total_weight: number;
  passed_weight: number;
  failed_weight: number;
  review_weight: number;
  summary_metrics?: {
    rules_count: number;
    passed_count: number;
    failed_count: number;
    review_count: number;
    breakdown?: any[];
    risk_reasons?: string[];
  };
  evaluated_at: string;
}

export interface ReviewDecision {
  id: string;
  bid_id: string;
  officer_id: string;
  officer_name?: string;
  decision: OfficerDecisionType;
  officer_notes: string;
  reviewed_at: string;
  created_at: string;
}

export interface Bid {
  id: string;
  tender_id: string;
  bidder_id: string;
  bid_number: string;
  bid_amount?: number;
  status: string;
  submitted_at: string;
  created_at: string;
  bidder?: Bidder;
  documents: Document[];
  compliance_assessment?: ComplianceAssessment;
  review_decisions: ReviewDecision[];
  rule_results?: RuleResult[];
}

export interface AuditEvent {
  id: string;
  timestamp: string;
  user_id?: string;
  user_name?: string;
  action: string;
  entity_type: string;
  entity_id: string;
  request_id?: string;
  metadata_json?: Record<string, any>;
}
