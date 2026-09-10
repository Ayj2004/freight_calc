from decimal import Decimal, ROUND_HALF_UP

def q2(x: Decimal) -> Decimal:
    """保留2位小数，四舍五入 HALF_UP"""
    return x.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

def compute_item(
    quantity: Decimal | None,
    unit_price: Decimal,
    pickup_fee: Decimal = Decimal("0"),
    surcharge: Decimal = Decimal("0"),
    buffer: Decimal = Decimal("0")
) -> tuple[Decimal | None, Decimal | None, Decimal | None]:
    """
    计算运费，与Postgres函数完全同构
    返回：(基础运费, 最低运费(底价), 运费合计(报价))
    quantity=None：未填写，返回None
    quantity=0：全部置0，不收取提送费
    """
    if quantity is None:
        return None, None, None

    base = q2(unit_price * quantity)
    sum_extra = pickup_fee + surcharge

    if quantity == Decimal("0"):
        return Decimal("0.00"), Decimal("0.00"), Decimal("0.00")

    lowest = q2(base + sum_extra)
    total = q2(base + sum_extra + buffer)
    return base, lowest, total

def suggest_surcharge(length_m: Decimal | None, is_irregular: bool, surcharge_rules: dict):
    """P1 自动推荐附加费，默认不启用，可在计算页面打开"""
    fee = Decimal("0")
    if length_m and length_m > Decimal("2.9"):
        over_rule = surcharge_rules.get("OVER_LENGTH", {})
        fee += Decimal(str(over_rule.get("default_fee", 0)))
    if is_irregular:
        irr_rule = surcharge_rules.get("IRREGULAR", {})
        fee += Decimal(str(irr_rule.get("default_fee", 0)))
    return fee
