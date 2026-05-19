from typing import Dict
from sqlalchemy import text


class FinaAuditServiceMixin:
    def get_fina_audit(self, ts_code: str, limit: int = 5) -> Dict:
        try:
            with self.engine.connect() as conn:
                query = text("""
                    SELECT ts_code, end_date, ann_date,
                           audit_result, audit_fees,
                           audit_agency, audit_sign
                    FROM fina_audit
                    WHERE ts_code = :ts_code
                    ORDER BY end_date DESC
                    LIMIT :limit
                """)
                result = conn.execute(query, {"ts_code": ts_code, "limit": limit})
                items = []
                for row in result:
                    items.append({
                        "ts_code": row.ts_code,
                        "end_date": row.end_date.strftime("%Y-%m-%d") if row.end_date else None,
                        "ann_date": row.ann_date.strftime("%Y-%m-%d") if row.ann_date else None,
                        "audit_result": row.audit_result,
                        "audit_fees": float(row.audit_fees) if row.audit_fees is not None else None,
                        "audit_agency": row.audit_agency,
                        "audit_sign": row.audit_sign,
                    })
                return {"success": True, "data": items}
        except Exception as e:
            return {"success": False, "error": str(e), "data": []}
