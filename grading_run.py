#!/usr/bin/env python3
"""
Chạy bộ câu grading — output JSONL cho giảng viên.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from providers import get_chroma_embedding_function, get_embedding_model_name, get_embedding_provider

load_dotenv()
ROOT = Path(__file__).resolve().parent


def summarize(records):
    total = len(records)
    passed = sum(1 for r in records if r["contains_expected"] and not r["hits_forbidden"])

    return {
        "total": total,
        "pass_rate": round(passed / total, 3) if total else 0,
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--questions", default=str(ROOT / "data" / "grading_questions.json"))
    p.add_argument("--out", default=str(ROOT / "artifacts" / "eval" / "grading_run.jsonl"))
    p.add_argument("--top-k", type=int, default=5)
    args = p.parse_args()

    try:
        import chromadb
    except ImportError:
        print("pip install chromadb sentence-transformers", file=sys.stderr)
        return 1

    qs = json.loads(Path(args.questions).read_text(encoding="utf-8"))

    db_path = os.environ.get("CHROMA_DB_PATH", str(ROOT / "chroma_db"))
    collection_name = os.environ.get("CHROMA_COLLECTION", "day10_kb")
    model_name = get_embedding_model_name()

    client = chromadb.PersistentClient(path=db_path)
    emb = get_chroma_embedding_function()
    col = client.get_collection(name=collection_name, embedding_function=emb)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    records = []

    with out.open("w", encoding="utf-8") as f:
        for q in qs:
            text = q["question"]

            res = col.query(query_texts=[text], n_results=args.top_k)
            docs = (res.get("documents") or [[]])[0]
            metas = (res.get("metadatas") or [[]])[0]

            blob = " ".join(docs).lower()

            must_any = [x.lower() for x in q.get("must_contain_any", [])]
            forbidden = [x.lower() for x in q.get("must_not_contain", [])]

            ok_any = any(m in blob for m in must_any) if must_any else True
            bad_forb = any(m in blob for m in forbidden) if forbidden else False

            top_doc = (metas[0] or {}).get("doc_id", "") if metas else ""
            want_top1 = (q.get("expect_top1_doc_id") or "").strip()

            top1_ok = True
            if want_top1:
                top1_ok = top_doc == want_top1

            # DEBUG
            print(f"\n[DEBUG] Q: {text}")
            print(f"Top doc: {top_doc}")
            print(f"Expected: {ok_any}, Forbidden: {bad_forb}")

            rec = {
                "id": q.get("id"),
                "question": text,
                "top1_doc_id": top_doc,
                "contains_expected": ok_any,
                "hits_forbidden": bad_forb,
                "top1_doc_matches": top1_ok if want_top1 else None,
                "top_k_used": args.top_k,
                "embedding_provider": get_embedding_provider(),
                "embedding_model": model_name,
                "grading_criteria": q.get("grading_criteria", []),
            }

            records.append(rec)
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    # ===== SUMMARY =====
    summary = summarize(records)

    print("\n=== GRADING SUMMARY ===")
    print(summary)

    print(f"\nWrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())