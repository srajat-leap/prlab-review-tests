from __future__ import annotations

from dataclasses import dataclass

from prlab_eval.judge import ClaimVerdict, quote_is_from_review, visible_review_text


@dataclass(frozen=True)
class CaseMetrics:
    true_positives: int = 0
    false_negatives: int = 0
    false_positives: int = 0
    relevant_comments: int = 0
    comments: int = 0
    precision: float = 0.0
    recall: float = 0.0
    f1: float = 0.0


def _ratio(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 0.0


def _f1(precision: float, recall: float) -> float:
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def review_comments(comments: tuple[str, ...] | list[str], fallback: str = "") -> list[str]:
    visible = [visible_review_text(item) for item in comments]
    visible = [item for item in visible if item]
    if visible:
        return visible
    fallback_text = visible_review_text(fallback)
    return [fallback_text] if fallback_text else []


def score_metrics(claims: list[ClaimVerdict], comments: list[str]) -> CaseMetrics:
    """Recall over expected claims; precision over actual PR comments.

    TP / FN are expected findings the review did or did not assert.
    FP are review comments that do not support any asserted expected finding.
    """
    claim_tp = sum(1 for claim in claims if claim.passed)
    claim_fn = sum(1 for claim in claims if not claim.passed)
    quotes = [claim.quote for claim in claims if claim.passed and claim.quote.strip()]

    comment_tp = 0
    comment_fp = 0
    for comment in comments:
        if quotes and any(quote_is_from_review(quote, comment) for quote in quotes):
            comment_tp += 1
        else:
            comment_fp += 1

    if claim_tp and comments and comment_tp == 0:
        comment_tp = 1
        comment_fp = max(0, len(comments) - 1)

    precision = _ratio(comment_tp, comment_tp + comment_fp)
    recall = _ratio(claim_tp, claim_tp + claim_fn)
    return CaseMetrics(
        true_positives=claim_tp,
        false_negatives=claim_fn,
        false_positives=comment_fp,
        relevant_comments=comment_tp,
        comments=len(comments),
        precision=precision,
        recall=recall,
        f1=_f1(precision, recall),
    )


def aggregate_metrics(rows: list[CaseMetrics]) -> CaseMetrics:
    tp = sum(row.true_positives for row in rows)
    fn = sum(row.false_negatives for row in rows)
    fp = sum(row.false_positives for row in rows)
    relevant = sum(row.relevant_comments for row in rows)
    comments = sum(row.comments for row in rows)
    precision = _ratio(relevant, comments)
    recall = _ratio(tp, tp + fn)
    return CaseMetrics(
        true_positives=tp,
        false_negatives=fn,
        false_positives=fp,
        relevant_comments=relevant,
        comments=comments,
        precision=precision,
        recall=recall,
        f1=_f1(precision, recall),
    )


def pct(value: float) -> str:
    return f"{value:.0%}"
