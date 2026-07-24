DISCOUNT_NONE = "none"
DISCOUNT_PERCENT = "percent"
DISCOUNT_AMOUNT = "amount"

DISCOUNT_TYPES = {DISCOUNT_NONE, DISCOUNT_PERCENT, DISCOUNT_AMOUNT}


def to_float(value, default=0.0) -> float:
    try:
        return float(value or default)
    except (TypeError, ValueError):
        return default


def normalize_discount_type(value) -> str:
    value = str(value or "").strip().lower()
    return value if value in DISCOUNT_TYPES else DISCOUNT_NONE


def normalize_discount_value(value) -> float:
    return max(0.0, to_float(value))


def calculate_discount_amount(subtotal, discount_type, discount_value) -> float:
    subtotal = max(0.0, to_float(subtotal))
    discount_type = normalize_discount_type(discount_type)
    discount_value = normalize_discount_value(discount_value)

    if subtotal <= 0 or discount_value <= 0 or discount_type == DISCOUNT_NONE:
        return 0.0
    if discount_type == DISCOUNT_PERCENT:
        return min(subtotal, subtotal * min(discount_value, 100.0) / 100.0)
    if discount_type == DISCOUNT_AMOUNT:
        return min(subtotal, discount_value)
    return 0.0


def apply_discount(subtotal, discount_type, discount_value) -> tuple[float, float]:
    discount_amount = calculate_discount_amount(subtotal, discount_type, discount_value)
    return discount_amount, max(0.0, to_float(subtotal) - discount_amount)


def prepare_item(item: dict) -> dict:
    prepared = dict(item)
    qty = to_float(prepared.get("qty"))
    price = to_float(prepared.get("price"))
    discount_type = normalize_discount_type(prepared.get("discount_type"))
    discount_value = normalize_discount_value(prepared.get("discount_value"))
    gross_sum = max(0.0, qty * price)
    discount_amount, net_sum = apply_discount(gross_sum, discount_type, discount_value)

    prepared["qty"] = qty
    prepared["price"] = price
    prepared["discount_type"] = discount_type
    prepared["discount_value"] = discount_value if discount_type != DISCOUNT_NONE else 0.0
    prepared["gross_sum"] = gross_sum
    prepared["discount_amount"] = discount_amount
    prepared["sum"] = net_sum
    return prepared


def summarize_items(items) -> tuple[list[dict], float, float, float]:
    prepared_items = [prepare_item(item) for item in items]
    gross_total = sum(item["gross_sum"] for item in prepared_items)
    line_discount_total = sum(item["discount_amount"] for item in prepared_items)
    net_total = sum(item["sum"] for item in prepared_items)
    return prepared_items, gross_total, line_discount_total, net_total


def calculate_invoice_totals(vehicle: dict, materials, works) -> dict:
    prepared_materials, materials_gross, materials_line_discount, materials_after_lines = summarize_items(materials)
    prepared_works, works_gross, works_line_discount, works_after_lines = summarize_items(works)

    materials_block_discount, materials_total = apply_discount(
        materials_after_lines,
        vehicle.get("materials_discount_type"),
        vehicle.get("materials_discount_value"),
    )
    works_block_discount, works_total = apply_discount(
        works_after_lines,
        vehicle.get("works_discount_type"),
        vehicle.get("works_discount_value"),
    )

    subtotal_after_blocks = materials_total + works_total
    invoice_discount, total = apply_discount(
        subtotal_after_blocks,
        vehicle.get("invoice_discount_type"),
        vehicle.get("invoice_discount_value"),
    )

    return {
        "materials": prepared_materials,
        "works": prepared_works,
        "materials_gross": materials_gross,
        "works_gross": works_gross,
        "materials_line_discount": materials_line_discount,
        "works_line_discount": works_line_discount,
        "materials_block_discount": materials_block_discount,
        "works_block_discount": works_block_discount,
        "materials_total": materials_total,
        "works_total": works_total,
        "subtotal_before_invoice_discount": subtotal_after_blocks,
        "invoice_discount": invoice_discount,
        "discount_total": (
            materials_line_discount
            + works_line_discount
            + materials_block_discount
            + works_block_discount
            + invoice_discount
        ),
        "total": total,
    }


def format_discount(discount_type, discount_value) -> str:
    discount_type = normalize_discount_type(discount_type)
    discount_value = normalize_discount_value(discount_value)
    if discount_type == DISCOUNT_PERCENT and discount_value > 0:
        return f"{discount_value:g} %"
    if discount_type == DISCOUNT_AMOUNT and discount_value > 0:
        return f"{discount_value:.2f} грн"
    return "Немає"
