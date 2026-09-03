"""Terminal menu-driven CLI for the procurement system."""

import sys
import textwrap
from db import init_db
import models


def clear():
    pass


def pause():
    input("\n按回车继续...")


def print_table(rows, headers):
    """Print a simple text table."""
    if not rows:
        print("  (无数据)")
        return
    col_widths = [len(h) for h in headers]
    str_rows = []
    for row in rows:
        sr = [str(v) if v is not None else "" for v in row]
        str_rows.append(sr)
        for i, v in enumerate(sr):
            col_widths[i] = max(col_widths[i], len(v))
    header_line = " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers))
    sep_line = "-+-".join("-" * col_widths[i] for i in range(len(headers)))
    print(f"  {header_line}")
    print(f"  {sep_line}")
    for sr in str_rows:
        line = " | ".join(sr[i].ljust(col_widths[i]) for i in range(len(headers)))
        print(f"  {line}")


def input_int(prompt, allow_empty=False):
    while True:
        val = input(prompt).strip()
        if allow_empty and val == "":
            return None
        try:
            return int(val)
        except ValueError:
            print("  请输入有效的整数")


def input_float(prompt, allow_empty=False):
    while True:
        val = input(prompt).strip()
        if allow_empty and val == "":
            return None
        try:
            return float(val)
        except ValueError:
            print("  请输入有效的数字")


# ─── Supplier Management ───────────────────────────────────

def supplier_menu():
    while True:
        print("\n--- 供应商管理 ---")
        print("1. 查看所有供应商")
        print("2. 添加供应商")
        print("3. 更新供应商")
        print("4. 删除供应商")
        print("0. 返回上级")
        choice = input("请选择: ").strip()
        if choice == "1":
            suppliers = models.get_all_suppliers()
            print_table(
                suppliers,
                ["ID", "名称", "联系人", "电话", "地址", "创建时间"],
            )
            pause()
        elif choice == "2":
            name = input("供应商名称: ").strip()
            if not name:
                print("  名称不能为空"); continue
            contact = input("联系人 (可选): ").strip() or None
            phone = input("电话 (可选): ").strip() or None
            address = input("地址 (可选): ").strip() or None
            sid = models.add_supplier(name, contact, phone, address)
            print(f"  供应商添加成功，ID: {sid}")
            pause()
        elif choice == "3":
            sid = input_int("要更新的供应商 ID: ")
            s = models.get_supplier(sid)
            if not s:
                print("  供应商不存在"); pause(); continue
            print(f"  当前: 名称={s['name']}, 联系人={s['contact']}, 电话={s['phone']}, 地址={s['address']}")
            name = input(f"新名称 (回车跳过): ").strip() or None
            contact = input("新联系人 (回车跳过): ").strip() or None
            phone = input("新电话 (回车跳过): ").strip() or None
            address = input("新地址 (回车跳过): ").strip() or None
            models.update_supplier(sid, name=name, contact=contact, phone=phone, address=address)
            print("  更新成功")
            pause()
        elif choice == "4":
            sid = input_int("要删除的供应商 ID: ")
            s = models.get_supplier(sid)
            if not s:
                print("  供应商不存在"); pause(); continue
            confirm = input(f"确认删除供应商 '{s['name']}'? (y/n): ").strip().lower()
            if confirm == "y":
                models.delete_supplier(sid)
                print("  已删除")
            else:
                print("  已取消")
            pause()
        elif choice == "0":
            break


# ─── Product Management ────────────────────────────────────

def product_menu():
    while True:
        print("\n--- 商品管理 ---")
        print("1. 查看所有商品")
        print("2. 添加商品")
        print("3. 更新商品")
        print("4. 删除商品")
        print("0. 返回上级")
        choice = input("请选择: ").strip()
        if choice == "1":
            products = models.get_all_products()
            print_table(
                products,
                ["ID", "名称", "单位", "单价", "库存", "创建时间"],
            )
            pause()
        elif choice == "2":
            name = input("商品名称: ").strip()
            if not name:
                print("  名称不能为空"); continue
            unit = input("单位: ").strip()
            if not unit:
                print("  单位不能为空"); continue
            price = input_float("单价: ")
            if price is None or price < 0:
                print("  无效单价"); continue
            stock = input_int("库存 (默认0): ", allow_empty=True) or 0
            pid = models.add_product(name, unit, price, stock)
            print(f"  商品添加成功，ID: {pid}")
            pause()
        elif choice == "3":
            pid = input_int("要更新的商品 ID: ")
            p = models.get_product(pid)
            if not p:
                print("  商品不存在"); pause(); continue
            print(f"  当前: 名称={p['name']}, 单位={p['unit']}, 单价={p['price']}, 库存={p['stock']}")
            name = input("新名称 (回车跳过): ").strip() or None
            unit = input("新单位 (回车跳过): ").strip() or None
            price = input_float("新单价 (回车跳过): ", allow_empty=True)
            stock = input_int("新库存 (回车跳过): ", allow_empty=True)
            models.update_product(pid, name=name, unit=unit, price=price, stock=stock)
            print("  更新成功")
            pause()
        elif choice == "4":
            pid = input_int("要删除的商品 ID: ")
            p = models.get_product(pid)
            if not p:
                print("  商品不存在"); pause(); continue
            confirm = input(f"确认删除商品 '{p['name']}'? (y/n): ").strip().lower()
            if confirm == "y":
                models.delete_product(pid)
                print("  已删除")
            else:
                print("  已取消")
            pause()
        elif choice == "0":
            break


# ─── Purchase Order Management ─────────────────────────────

def order_menu():
    while True:
        print("\n--- 采购订单管理 ---")
        print("1. 查看所有订单")
        print("2. 创建新订单")
        print("3. 查看订单详情")
        print("4. 更新订单状态")
        print("5. 删除订单")
        print("0. 返回上级")
        choice = input("请选择: ").strip()
        if choice == "1":
            orders = models.get_all_orders()
            print_table(
                orders,
                ["订单ID", "供应商", "总金额", "状态", "创建时间"],
            )
            pause()
        elif choice == "2":
            suppliers = models.get_all_suppliers()
            if not suppliers:
                print("  请先添加供应商"); pause(); continue
            print_table(suppliers, ["ID", "名称", "联系人", "电话", "地址", "创建时间"])
            sid = input_int("选择供应商 ID: ")
            s = models.get_supplier(sid)
            if not s:
                print("  供应商不存在"); pause(); continue
            oid = models.create_order(sid)
            print(f"  订单 {oid} 已创建，开始添加商品:")
            while True:
                products = models.get_all_products()
                if not products:
                    print("  无可用商品，请先添加商品"); break
                print_table(products, ["ID", "名称", "单位", "单价", "库存", "创建时间"])
                pid = input_int("商品 ID (输入0完成): ")
                if pid == 0:
                    break
                p = models.get_product(pid)
                if not p:
                    print("  商品不存在"); continue
                qty = input_int("数量: ")
                if qty is not None and qty <= 0:
                    print("  数量必须大于0"); continue
                uprice = input_float("单价 (回车使用商品默认价): ", allow_empty=True)
                if uprice is None:
                    uprice = p["price"]
                models.add_order_item(oid, pid, qty, uprice)
                print(f"  已添加: {p['name']} x{qty}")
            order = models.get_order(oid)
            print(f"  订单 {oid} 总金额: {order['total_amount']}")
            pause()
        elif choice == "3":
            oid = input_int("订单 ID: ")
            order = models.get_order(oid)
            if not order:
                print("  订单不存在"); pause(); continue
            print(f"\n  订单 #{order['id']} | 供应商: {order['supplier_name']} | 总金额: {order['total_amount']} | 状态: {order['status']} | 创建: {order['created_at']}")
            items = models.get_order_items(oid)
            print_table(
                items,
                ["项目ID", "订单ID", "商品ID", "商品名称", "单位", "数量", "单价", "小计"],
            )
            pause()
        elif choice == "4":
            oid = input_int("订单 ID: ")
            order = models.get_order(oid)
            if not order:
                print("  订单不存在"); pause(); continue
            print(f"  当前状态: {order['status']}")
            print("  可选状态: pending / confirmed / shipped / received / cancelled")
            status = input("新状态: ").strip()
            if status not in ("pending", "confirmed", "shipped", "received", "cancelled"):
                print("  无效状态"); pause(); continue
            models.update_order_status(oid, status)
            print("  状态已更新")
            pause()
        elif choice == "5":
            oid = input_int("要删除的订单 ID: ")
            order = models.get_order(oid)
            if not order:
                print("  订单不存在"); pause(); continue
            confirm = input(f"确认删除订单 #{oid}? (y/n): ").strip().lower()
            if confirm == "y":
                models.delete_order(oid)
                print("  已删除")
            else:
                print("  已取消")
            pause()
        elif choice == "0":
            break


# ─── User Management ───────────────────────────────────────

def register():
    """Register a new user."""
    print("\n--- 用户注册 ---")
    username = input("用户名: ").strip()
    if not username:
        print("  用户名不能为空")
        return None
    if models.get_user_by_username(username):
        print("  用户名已存在")
        return None
    password = input("密码: ").strip()
    if not password:
        print("  密码不能为空")
        return None
    password2 = input("确认密码: ").strip()
    if password != password2:
        print("  两次密码不一致")
        return None
    display_name = input("显示名称 (可选): ").strip() or None
    uid = models.add_user(username, password, display_name)
    if uid:
        print(f"  注册成功！欢迎 {username}")
        return models.get_user_by_username(username)
    else:
        print("  注册失败")
        return None


def login():
    """Login and return the user object, or None."""
    print("\n--- 用户登录 ---")
    username = input("用户名: ").strip()
    password = input("密码: ").strip()
    user = models.verify_user(username, password)
    if user:
        name = user["display_name"] or user["username"]
        print(f"  登录成功！欢迎 {name}")
        return user
    else:
        print("  用户名或密码错误")
        return None


def auth_menu():
    """Login/Register screen. Returns a user dict on success, or None to exit."""
    while True:
        print("\n===== 采购管理系统 =====")
        print("1. 登录")
        print("2. 注册")
        print("0. 退出")
        choice = input("请选择: ").strip()
        if choice == "1":
            user = login()
            if user:
                return user
        elif choice == "2":
            user = register()
            if user:
                return user
        elif choice == "0":
            print("再见!")
            sys.exit(0)
        else:
            print("  无效选择")


# ─── Kanban Board ──────────────────────────────────────────

def print_kanban_card(order, max_width=28):
    """Print a single order card inside a kanban column."""
    lines = [
        f"#{order['id']} {order['supplier_name']}",
        f"¥{order['total_amount']:.2f}  |  {order['item_count']}项",
        f"{order['created_at'][:10] if order['created_at'] else ''}",
    ]
    # Wrap long supplier names
    wrapped = []
    for line in lines:
        if len(line) > max_width - 2:
            wrapped.append(line[:max_width - 5] + "...")
        else:
            wrapped.append(line)
    # Pad and print card
    print("  ┌" + "─" * max_width + "┐")
    for line in wrapped:
        print(f"  │ {line:<{max_width}} │")
    print("  └" + "─" * max_width + "┘")


def print_kanban_column(label, orders, col_width=32):
    """Print one kanban column with header and cards."""
    header = f"【{label}】({len(orders)})"
    print(f"\n{header}")
    print("  " + "─" * col_width)
    if not orders:
        print("  (空)")
    else:
        for order in orders:
            print_kanban_card(order, max_width=col_width - 2)
    print()


def kanban_menu():
    """Interactive kanban board showing purchase orders grouped by status."""
    # Single-column view: user picks which status to view
    columns = models.KANBAN_COLUMNS
    labels = models.KANBAN_LABELS
    while True:
        print("\n--- 采购订单看板 ---")
        print("  显示模式:")
        print("1. 单列查看 (选择一个状态)")
        print("2. 全部概览 (所有状态并排)")
        print("0. 返回上级")
        choice = input("请选择: ").strip()
        if choice == "1":
            print("\n  可选状态:")
            for i, col in enumerate(columns, 1):
                orders = models.get_orders_by_status(col)
                print(f"  {i}. {labels[col]} ({len(orders)}个)")
            idx = input_int("选择状态编号: ")
            if idx is None or idx < 1 or idx > len(columns):
                print("  无效选择"); continue
            status = columns[idx - 1]
            orders = models.get_orders_by_status(status)
            print_kanban_column(labels[status], orders)
            pause()
        elif choice == "2":
            kanban_data = models.get_kanban_data()
            for label in [labels[c] for c in columns]:
                orders = kanban_data.get(label, [])
                print_kanban_column(label, orders)
            pause()
        elif choice == "0":
            break
        else:
            print("  无效选择")


# ─── Main ──────────────────────────────────────────────────

def main():
    init_db()
    print("=" * 30)
    print("   采购管理系统")
    print("=" * 30)

    # Login first
    user = auth_menu()

    while True:
        print(f"\n===== 采购管理系统 ({user['username']}) =====")
        print("1. 供应商管理")
        print("2. 商品管理")
        print("3. 采购订单管理")
        print("4. 采购看板")
        print("5. 退出登录")
        print("0. 退出系统")
        choice = input("请选择: ").strip()
        if choice == "1":
            supplier_menu()
        elif choice == "2":
            product_menu()
        elif choice == "3":
            order_menu()
        elif choice == "4":
            kanban_menu()
        elif choice == "5":
            print("已退出登录")
            user = auth_menu()
        elif choice == "0":
            print("再见!")
            sys.exit(0)
        else:
            print("  无效选择")


if __name__ == "__main__":
    main()
