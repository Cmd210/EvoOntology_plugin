"""生成示例业务数据库 demo_business.db（模拟用户的真实数据源）。

一个简单的销售分析场景：customers / products / sales 三张表，含退款标记，
让 Builder 能探索出 region/category 维度、revenue/profit 指标与 refund 约束。
"""

import os
import sqlite3

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "demo_business.db")


def main() -> None:
    if os.path.exists(DB):
        os.remove(DB)

    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.executescript(
        """
        CREATE TABLE customers (
            customer_id INTEGER PRIMARY KEY,
            name        TEXT,
            region      TEXT
        );

        CREATE TABLE products (
            product_id INTEGER PRIMARY KEY,
            name       TEXT,
            category   TEXT,
            unit_cost  REAL,
            unit_price REAL
        );

        CREATE TABLE sales (
            sale_id     INTEGER PRIMARY KEY,
            customer_id INTEGER,
            product_id  INTEGER,
            sale_date   TEXT,
            quantity    INTEGER,
            amount      REAL,
            is_refund   INTEGER
        );
        """
    )

    customers = [
        (1, "Alpha Corp", "North"),
        (2, "Beta Ltd", "South"),
        (3, "Gamma Inc", "North"),
        (4, "Delta LLC", "East"),
    ]
    products = [
        (1, "Widget", "Hardware", 5.0, 12.0),
        (2, "Gadget", "Hardware", 8.0, 20.0),
        (3, "Gizmo", "Software", 3.0, 15.0),
        (4, "Doodad", "Software", 2.0, 9.0),
    ]
    sales = [
        (1, 1, 1, "2026-01-05", 10, 120.0, 0),
        (2, 1, 2, "2026-01-06", 5, 100.0, 0),
        (3, 2, 3, "2026-01-07", 8, 120.0, 0),
        (4, 3, 1, "2026-01-08", 6, 72.0, 0),
        (5, 4, 4, "2026-01-09", 20, 180.0, 0),
        (6, 1, 1, "2026-01-12", 2, 24.0, 1),  # 退款
        (7, 2, 2, "2026-01-13", 4, 80.0, 0),
        (8, 3, 4, "2026-01-14", 10, 90.0, 0),
    ]

    cur.executemany(
        "INSERT INTO customers (customer_id, name, region) VALUES (?, ?, ?)",
        customers,
    )
    cur.executemany(
        "INSERT INTO products (product_id, name, category, unit_cost, unit_price) "
        "VALUES (?, ?, ?, ?, ?)",
        products,
    )
    cur.executemany(
        "INSERT INTO sales (sale_id, customer_id, product_id, sale_date, quantity, "
        "amount, is_refund) VALUES (?, ?, ?, ?, ?, ?, ?)",
        sales,
    )

    conn.commit()
    conn.close()
    print(f"已生成示例数据库: {DB}")


if __name__ == "__main__":
    main()
