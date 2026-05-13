import random
import sqlite3
import time
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import streamlit as st

DB_PATH = Path("llm_monitor.db")

MODEL_COSTS = {
    "gpt-4.1": {"input_per_1m": 2.00, "output_per_1m": 8.00},
    "gpt-4.1-mini": {"input_per_1m": 0.40, "output_per_1m": 1.60},
    "claude-sonnet": {"input_per_1m": 3.00, "output_per_1m": 15.00},
    "llama-70b-vllm": {"input_per_1m": 0.20, "output_per_1m": 0.20},
    "llama-8b-vllm": {"input_per_1m": 0.05, "output_per_1m": 0.05},
}

TASKS = [
    "rag_answer",
    "document_extraction",
    "agent_tool_call",
    "classification",
    "summarization",
    "code_generation",
]

STATUSES = ["success", "success", "success", "success", "fallback", "error"]


def init_db() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS llm_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts TEXT NOT NULL,
            model TEXT NOT NULL,
            task TEXT NOT NULL,
            input_tokens INTEGER NOT NULL,
            output_tokens INTEGER NOT NULL,
            latency_ms INTEGER NOT NULL,
            cost_usd REAL NOT NULL,
            status TEXT NOT NULL,
            cache_hit INTEGER NOT NULL,
            eval_score REAL NOT NULL,
            prompt_injection_flag INTEGER NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    pricing = MODEL_COSTS[model]
    return round(
        (input_tokens / 1_000_000) * pricing["input_per_1m"]
        + (output_tokens / 1_000_000) * pricing["output_per_1m"],
        6,
    )


def insert_event(event: dict) -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        INSERT INTO llm_events (
            ts, model, task, input_tokens, output_tokens, latency_ms,
            cost_usd, status, cache_hit, eval_score, prompt_injection_flag
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            event["ts"],
            event["model"],
            event["task"],
            event["input_tokens"],
            event["output_tokens"],
            event["latency_ms"],
            event["cost_usd"],
            event["status"],
            event["cache_hit"],
            event["eval_score"],
            event["prompt_injection_flag"],
        ),
    )
    conn.commit()
    conn.close()


def load_events() -> pd.DataFrame:
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM llm_events ORDER BY ts DESC", conn)
    conn.close()
    return df


def generate_synthetic_events(n: int = 100) -> None:
    now = datetime.utcnow()
    models = list(MODEL_COSTS.keys())
    for _ in range(n):
        model = random.choice(models)
        task = random.choice(TASKS)
        cache_hit = 1 if random.random() < 0.28 else 0
        status = random.choice(STATUSES)
        input_tokens = random.randint(300, 8_000)
        output_tokens = random.randint(120, 2_500)
        base_latency = {
            "gpt-4.1": 2200,
            "gpt-4.1-mini": 800,
            "claude-sonnet": 2400,
            "llama-70b-vllm": 1200,
            "llama-8b-vllm": 450,
        }[model]
        latency_ms = max(80, int(random.gauss(base_latency, base_latency * 0.25)))
        if cache_hit:
            latency_ms = int(latency_ms * 0.35)
        eval_score = round(random.uniform(0.72, 0.98), 3)
        if status == "error":
            eval_score = round(random.uniform(0.0, 0.4), 3)
        prompt_injection_flag = 1 if random.random() < 0.04 else 0
        ts = now - timedelta(minutes=random.randint(0, 60 * 24))
        insert_event(
            {
                "ts": ts.isoformat(),
                "model": model,
                "task": task,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "latency_ms": latency_ms,
                "cost_usd": estimate_cost(model, input_tokens, output_tokens),
                "status": status,
                "cache_hit": cache_hit,
                "eval_score": eval_score,
                "prompt_injection_flag": prompt_injection_flag,
            }
        )


def reset_db() -> None:
    if DB_PATH.exists():
        DB_PATH.unlink()
    init_db()


def main() -> None:
    st.set_page_config(page_title="LLM Observability Monitor", layout="wide")
    init_db()

    st.title("LLM Observability Monitor")
    st.caption("Reference implementation for cost, latency, cache, failure, and evaluation monitoring in LLM applications.")

    with st.sidebar:
        st.header("Controls")
        if st.button("Generate synthetic events"):
            generate_synthetic_events(150)
            st.success("Synthetic LLM events generated")
            time.sleep(0.5)
            st.rerun()
        if st.button("Reset database"):
            reset_db()
            st.warning("Database reset")
            time.sleep(0.5)
            st.rerun()

        st.divider()
        st.subheader("Manual event")
        model = st.selectbox("Model", list(MODEL_COSTS.keys()))
        task = st.selectbox("Task", TASKS)
        input_tokens = st.number_input("Input tokens", min_value=1, value=1200)
        output_tokens = st.number_input("Output tokens", min_value=1, value=450)
        latency_ms = st.number_input("Latency ms", min_value=1, value=850)
        status = st.selectbox("Status", ["success", "fallback", "error"])
        cache_hit = st.checkbox("Cache hit")
        eval_score = st.slider("Eval score", 0.0, 1.0, 0.88)
        injection_flag = st.checkbox("Prompt injection flagged")
        if st.button("Insert manual event"):
            insert_event(
                {
                    "ts": datetime.utcnow().isoformat(),
                    "model": model,
                    "task": task,
                    "input_tokens": int(input_tokens),
                    "output_tokens": int(output_tokens),
                    "latency_ms": int(latency_ms),
                    "cost_usd": estimate_cost(model, int(input_tokens), int(output_tokens)),
                    "status": status,
                    "cache_hit": int(cache_hit),
                    "eval_score": float(eval_score),
                    "prompt_injection_flag": int(injection_flag),
                }
            )
            st.success("Event inserted")
            st.rerun()

    df = load_events()
    if df.empty:
        st.info("No events yet. Generate synthetic events from the sidebar.")
        return

    total_requests = len(df)
    total_cost = df["cost_usd"].sum()
    avg_latency = df["latency_ms"].mean()
    p95_latency = df["latency_ms"].quantile(0.95)
    cache_rate = df["cache_hit"].mean() * 100
    error_rate = (df["status"] == "error").mean() * 100
    fallback_rate = (df["status"] == "fallback").mean() * 100
    avg_eval = df["eval_score"].mean()
    injection_count = int(df["prompt_injection_flag"].sum())

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Requests", f"{total_requests:,}")
    c2.metric("Total cost", f"${total_cost:.4f}")
    c3.metric("Avg latency", f"{avg_latency:.0f} ms")
    c4.metric("p95 latency", f"{p95_latency:.0f} ms")

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Cache hit rate", f"{cache_rate:.1f}%")
    c6.metric("Error rate", f"{error_rate:.1f}%")
    c7.metric("Fallback rate", f"{fallback_rate:.1f}%")
    c8.metric("Avg eval score", f"{avg_eval:.2f}")

    if injection_count:
        st.warning(f"Prompt-injection flags detected: {injection_count}")

    st.subheader("Cost by model")
    cost_by_model = df.groupby("model", as_index=False)["cost_usd"].sum().sort_values("cost_usd", ascending=False)
    st.bar_chart(cost_by_model, x="model", y="cost_usd")

    st.subheader("Latency by model")
    latency_by_model = df.groupby("model", as_index=False)["latency_ms"].mean().sort_values("latency_ms", ascending=False)
    st.bar_chart(latency_by_model, x="model", y="latency_ms")

    st.subheader("Status distribution")
    status_counts = df["status"].value_counts().reset_index()
    status_counts.columns = ["status", "count"]
    st.bar_chart(status_counts, x="status", y="count")

    st.subheader("Recent events")
    st.dataframe(df.head(100), use_container_width=True)

    st.subheader("Operational interpretation")
    st.markdown(
        """
        This dashboard demonstrates the minimum signals a serious LLM application should track:

        - Cost is not just model pricing; retries, long prompts, and cache misses drive spend.
        - Latency must be tracked by model, task type, and cache status.
        - Evaluation score gives a quality trend, not a perfect truth signal.
        - Fallback and error rates expose model/provider instability.
        - Prompt-injection flags need to be visible before tool execution becomes dangerous.
        """
    )


if __name__ == "__main__":
    main()
