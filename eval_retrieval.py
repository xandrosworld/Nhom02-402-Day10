#!/usr/bin/env python3
"""
Đánh giá retrieval đơn giản — before/after khi pipeline đổi dữ liệu embed.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from providers import call_llm_json, get_chroma_embedding_function, get_embedding_model_name, get_embedding_provider

load_dotenv()

ROOT = Path(__file__).resolve().parent


def llm_judge(question: str, docs: list[str], *, must_any: list[str], forbidden: list[str]) -> dict[str, str]:
    system_prompt = (
        "You are a strict retrieval evaluator. "
        "Return valid JSON only with keys: grounded, mentions_expected, mentions_forbidden, note."
    )
    docs_blob = "\n\n".join(f"[doc {i + 1}] {doc}" for i, doc in enumerate(docs)) or "(empty)"
    user_prompt = f"""Question: {question}

Expected phrases: {must_any}
Forbidden phrases: {forbidden}

Retrieved documents:
{docs_blob}

Judge whether the retrieved documents support the expected answer and avoid stale or forbidden evidence.
Return JSON only:
{{
  "grounded": "yes|no",
  "mentions_expected": "yes|no",
  "mentions_forbidden": "yes|no",
  "note": "short explanation"
}}"""
    result = call_llm_json(system_prompt=system_prompt, user_prompt=user_prompt, max_tokens=220)
    return {
        "grounded": str(result.get("grounded", "no")),
        "mentions_expected": str(result.get("mentions_expected", "no")),
        "mentions_forbidden": str(result.get("mentions_forbidden", "no")),
        "note": str(result.get("note", "")),
    }


def summarize(rows):
    total = len(rows)
    correct = sum(1 for r in rows if r["contains_expected"] == "yes")
    forbidden = sum(1 for r in rows if r["hits_forbidden"] == "yes")

    return {
        "total": total,
        "hit_correct_rate": round(correct / total, 3) if total else 0,
        "hits_forbidden_rate": round(forbidden / total, 3) if total else 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--questions",
        default=str(ROOT / "data" / "test_questions.json"),
    )
    parser.add_argument(
        "--out",
        default=str(ROOT / "artifacts" / "eval" / "before_after_eval.csv"),
    )
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--llm-judge", action="store_true")
    args = parser.parse_args()

    try:
        import chromadb
    except ImportError:
        print("Install: pip install chromadb sentence-transformers", file=sys.stderr)
        return 1

    qpath = Path(args.questions)
    if not qpath.is_file():
        print(f"questions not found: {qpath}", file=sys.stderr)
        return 1

    questions = json.loads(qpath.read_text(encoding="utf-8"))
    db_path = os.environ.get("CHROMA_DB_PATH", str(ROOT / "chroma_db"))
    collection_name = os.environ.get("CHROMA_COLLECTION", "day10_kb")
    model_name = get_embedding_model_name()

    client = chromadb.PersistentClient(path=db_path)
    emb = get_chroma_embedding_function()

    try:
        col = client.get_collection(name=collection_name, embedding_function=emb)
    except Exception as e:
        print(f"Collection error: {e}", file=sys.stderr)
        return 2

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "question_id",
        "question",
        "top1_doc_id",
        "top1_preview",
        "contains_expected",
        "hits_forbidden",
        "top1_doc_expected",
        "top_k_used",
        "embedding_provider",
        "embedding_model",
        "llm_judge_grounded",
        "llm_judge_note",
    ]

    rows = []

    with out_path.open("w", encoding="utf-8", newline="") as fcsv:
        w = csv.DictWriter(fcsv, fieldnames=fieldnames)
        w.writeheader()

        for q in questions:
            text = q["question"]

            res = col.query(query_texts=[text], n_results=args.top_k)
            docs = (res.get("documents") or [[]])[0]
            metas = (res.get("metadatas") or [[]])[0]

            top_doc = (metas[0] or {}).get("doc_id", "") if metas else ""
            preview = (docs[0] or "")[:180].replace("\n", " ") if docs else ""

            blob = " ".join(docs).lower()
            must_any = [x.lower() for x in q.get("must_contain_any", [])]
            forbidden = [x.lower() for x in q.get("must_not_contain", [])]

            ok_any = any(m in blob for m in must_any) if must_any else True
            bad_forb = any(m in blob for m in forbidden) if forbidden else False

            # DEBUG (rất hữu ích khi demo)
            print(f"\n[DEBUG] Q: {text}")
            print(f"Top docs: {docs[:2]}")
            print(f"Expected match: {ok_any}, Forbidden hit: {bad_forb}")

            want_top1 = (q.get("expect_top1_doc_id") or "").strip()
            top1_expected = ""
            if want_top1:
                top1_expected = "yes" if top_doc == want_top1 else "no"

            llm_grounded = ""
            llm_note = ""

            if args.llm_judge:
                try:
                    judged = llm_judge(text, docs, must_any=must_any, forbidden=forbidden)
                    llm_grounded = judged["grounded"]
                    llm_note = judged["note"]
                except Exception as e:
                    llm_grounded = "error"
                    llm_note = str(e)

            row = {
                "question_id": q.get("id", ""),
                "question": text,
                "top1_doc_id": top_doc,
                "top1_preview": preview,
                "contains_expected": "yes" if ok_any else "no",
                "hits_forbidden": "yes" if bad_forb else "no",
                "top1_doc_expected": top1_expected,
                "top_k_used": args.top_k,
                "embedding_provider": get_embedding_provider(),
                "embedding_model": model_name,
                "llm_judge_grounded": llm_grounded,
                "llm_judge_note": llm_note,
            }

            rows.append(row)
            w.writerow(row)

    # ===== SUMMARY =====
    summary = summarize(rows)
    print("\n=== EVAL SUMMARY ===")
    print(summary)

    print(f"\nWrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())