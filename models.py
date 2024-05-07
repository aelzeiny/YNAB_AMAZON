from pydantic import BaseModel, model_validator, field_serializer
from decimal import Decimal
import datetime as dt
from typing import Optional


class Item(BaseModel):
    price: Decimal
    title: str
    short_name: str

    def adjusted_cost(self, receipt: "Receipt") -> Decimal:
        """The "adjusted cost" of an item accounts for taxes and discounts.
        For example, a 5% discount applies to all items equally."""
        return round(self.price / receipt.item_subtotal() * receipt.grand_total, 2)


class Receipt(BaseModel):
    items: list[Item]
    total_before_tax: Decimal
    subtotal: Decimal
    grand_total: Decimal
    date: dt.date

    def item_subtotal(self):
        return sum(i.price for i in self.items)


class SaveSubTransaction(BaseModel):
    amount: int
    memo: str  # name of thing

    @classmethod
    def from_item(cls, receipt: Receipt, item: Item):
        return cls(
            amount=-abs(int(round(item.adjusted_cost(receipt) * 1000))),
            memo=item.short_name,
        )


class NewTransaction(BaseModel):
    account_id: str  # uuid
    date: dt.date
    amount: int
    payee_name: str
    memo: Optional[str]  # should be the order_id
    subtransactions: list[SaveSubTransaction]

    @field_serializer("date")
    def serialize_dt(self, date: dt.date, *_, **__):
        return str(date)  # %Y-%m-%d

    @classmethod
    def from_receipt(
        cls, order_id: str, account_id: str, payee_name: str, receipt: Receipt
    ) -> "NewTransaction":
        subtransactions = [
            SaveSubTransaction.from_item(receipt, item) for item in receipt.items
        ]
        return cls(
            account_id=account_id,
            date=receipt.date,
            amount=-abs(int(round(receipt.grand_total * 1000))),
            payee_name=payee_name,
            subtransactions=subtransactions,
            memo=order_id,
        )

