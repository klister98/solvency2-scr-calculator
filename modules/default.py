"""Counterparty default risk - type 2 exposures only in v1 (Art. 202).

Type 1 exposures (cash at banks, reinsurance, derivatives) need counterparty
ratings and the loss-given-default formula; they are a planned extension.
"""
import params as P


def default(ins) -> dict:
    current = ins.other.receivables_current * P.TYPE2_FACTOR
    overdue = ins.other.receivables_overdue * P.TYPE2_OVERDUE_INTERMEDIARY_FACTOR
    return {"charge": current + overdue, "type2_current": current, "type2_overdue": overdue}
