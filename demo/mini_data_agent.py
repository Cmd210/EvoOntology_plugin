"""迷你 Data Agent：模拟真实 Data Agent 跑一轮任务并记录 Tool Call 级轨迹。

对每个任务依次调用 browse_semantics / resolve_semantics（语义工具）与
execute_sql（原生工具），把完整 tool_calls 序列 + final_answer 追加到
``.evoontology/trajectories/``，作为后续 /evo-evolve 的诊断输入。

运行前需先完成 /evo-build（生成 .evoontology/semantic_v0），并已生成
demo_business.db（python make_db.py）。
"""

import json
import os
import sqlite3

from evoontology import SemanticLayer, TrajectoryStore, truncate_result

BASE = os.path.dirname(os.path.abspath(__file__))
WORKSPACE = os.path.join(BASE, ".evoontology")
DB = os.path.join(BASE, "demo_business.db")

# (task_id, question, browse_query, resolve_mentions, sql)
TASKS = [
    (
        "task_001",
        "各地区的总销售额是多少？",
        "地区 销售额",
        ["sales", "region"],
        "SELECT c.region, SUM(s.amount) AS total_sales "
        "FROM sales s JOIN customers c ON s.customer_id = c.customer_id "
        "GROUP BY c.region ORDER BY total_sales DESC",
    ),
    (
        "task_002",
        "North 区域的净收入（排除退款）是多少？",
        "净收入 退款",
        ["revenue", "refund"],
        "SELECT SUM(s.amount) AS net_revenue "
        "FROM sales s JOIN customers c ON s.customer_id = c.customer_id "
        "WHERE c.region = 'North' AND s.is_refund = 0",
    ),
    (
        "task_003",
        "哪个产品类别的销量最高？",
        "产品类别 销量",
        ["category", "quantity"],
        "SELECT p.category, SUM(s.quantity) AS total_qty "
        "FROM sales s JOIN products p ON s.product_id = p.product_id "
        "GROUP BY p.category ORDER BY total_qty DESC",
    ),
    (
        "task_004",
        "Hardware 类产品的利润（收入 - 成本）是多少？",
        "利润 成本",
        ["profit", "category"],
        "SELECT SUM(s.amount - p.unit_cost * s.quantity) AS profit "
        "FROM sales s JOIN products p ON s.product_id = p.product_id "
        "WHERE p.category = 'Hardware' AND s.is_refund = 0",
    ),
    (
        "task_005",
        "每个客户的平均订单金额是多少？",
        "客户 平均订单金额",
        ["customer"],
        "SELECT c.name, ROUND(AVG(s.amount), 2) AS avg_order "
        "FROM sales s JOIN customers c ON s.customer_id = c.customer_id "
        "GROUP BY c.customer_id ORDER BY avg_order DESC",
    ),
]


def run_sql(sql: str):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    cols = [d[0] for d in cur.description]
    conn.close()
    return {"columns": cols, "rows": rows}


def main() -> None:
    layer = SemanticLayer.load(WORKSPACE)
    store = TrajectoryStore(WORKSPACE)

    for task_id, question, browse_q, mentions, sql in TASKS:
        tool_calls = []
        step = 0

        step += 1
        br = layer.browse(query=browse_q)
        tool_calls.append({
            "step": step, "category": "semantic", "tool_name": "browse_semantics",
            "arguments": {"query": browse_q}, "result": br, "error": None,
        })

        step += 1
        rs = layer.resolve(mentions=mentions)
        tool_calls.append({
            "step": step, "category": "semantic", "tool_name": "resolve_semantics",
            "arguments": {"mentions": mentions}, "result": rs, "error": None,
        })

        step += 1
        data = run_sql(sql)
        tool_calls.append({
            "step": step, "category": "native", "tool_name": "execute_sql",
            "arguments": {"sql": sql}, "result": truncate_result(data), "error": None,
        })

        store.append({
            "task_id": task_id,
            "question": question,
            "ontology_version": layer.version,
            "tool_calls": tool_calls,
            "final_answer": json.dumps(data, ensure_ascii=False),
            "status": "completed",
        })
        print(f"[{task_id}] {question}")
        print(f"    -> {data['columns']} {data['rows']}")

    print(f"\n已记录 {store.count_since(None)} 条轨迹 -> {WORKSPACE}/trajectories/")


if __name__ == "__main__":
    main()
