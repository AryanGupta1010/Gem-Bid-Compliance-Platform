from typing import List, Dict, Any, Tuple
from app.models import RuleStatus, Severity
from app.rules.engine import RuleResultDTO

SEVERITY_WEIGHTS: Dict[Severity, float] = {
    Severity.CRITICAL: 30.0,
    Severity.HIGH: 20.0,
    Severity.MEDIUM: 10.0,
    Severity.LOW: 5.0,
}

class ScoringService:
    def calculate_score(self, rule_results: List[RuleResultDTO]) -> Tuple[float, float, float, float, float, List[Dict[str, Any]]]:
        """
        Calculates explainable compliance score and returns:
        (compliance_score, total_weight, passed_weight, failed_weight, review_weight, breakdown)
        """
        total_possible_weight = 0.0
        passed_weight = 0.0
        failed_weight = 0.0
        review_weight = 0.0
        breakdown = []

        for res in rule_results:
            weight = getattr(res, "weight", None)
            if not weight or weight <= 0:
                weight = SEVERITY_WEIGHTS.get(res.severity, 20.0)

            total_possible_weight += weight

            contributed = 0.0
            if res.status == RuleStatus.PASS:
                passed_weight += weight
                contributed = weight
            elif res.status == RuleStatus.FAIL:
                failed_weight += weight
                contributed = 0.0
            elif res.status in (RuleStatus.REVIEW, RuleStatus.UNAVAILABLE):
                review_weight += weight
                # Partial contribution for uncertain/reviewable items if non-critical
                contributed = 0.0

            breakdown.append({
                "requirement_id": res.requirement_id,
                "severity": res.severity.value if hasattr(res.severity, "value") else str(res.severity),
                "weight": weight,
                "status": res.status.value if hasattr(res.status, "value") else str(res.status),
                "contributed_weight": contributed
            })

        if total_possible_weight > 0:
            compliance_score = round((passed_weight / total_possible_weight) * 100.0, 2)
        else:
            compliance_score = 0.0

        return compliance_score, total_possible_weight, passed_weight, failed_weight, review_weight, breakdown

scoring_service = ScoringService()
