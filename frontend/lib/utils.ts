import type { Risk, Status } from "./types";
export const statusClass = (status: Status) => `status-${status.toLowerCase()}`;
export const riskClass = (risk: Risk) => `risk-${risk.toLowerCase()}`;
export const formatPercent = (value: number) => `${Math.round(value * 100)}%`;
