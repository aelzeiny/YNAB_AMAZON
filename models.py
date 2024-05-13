import re
from dataclasses import dataclass
from pydantic import BaseModel, field_serializer
from decimal import Decimal
import datetime as dt
from typing import Optional


# God help me
# https://stackoverflow.com/questions/33404752/removing-emojis-from-a-string-in-python
EMOJI_PATTERN = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F680-\U0001F6FF"  # transport & map symbols
    "\U0001F1E0-\U0001F1FF"  # flags (iOS)
    "\U00002500-\U00002BEF"  # chinese char
    "\U00002702-\U000027B0"
    "\U000024C2-\U0001F251"
    "\U0001f926-\U0001f937"
    "\U00010000-\U0010ffff"
    "\u2640-\u2642"
    "\u2600-\u2B55"
    "\u200d"
    "\u23cf"
    "\u23e9"
    "\u231a"
    "\ufe0f"  # dingbats
    "\u3030"
    "]+",
    re.UNICODE,
)


@dataclass
class Category:
    group: str
    name: str
    category_id: str

    def full_name(self) -> str:
        return f"{self.group}/{self.get_name()}"

    def get_name(self) -> str:
        return EMOJI_PATTERN.sub("", self.name).strip().lower()


class Item(BaseModel):
    price: Decimal
    title: str
    short_name: str
    category: str
    _ynab_category: Optional[Category] = None

    def adjusted_cost(self, receipt: "Receipt") -> Decimal:
        """The "adjusted cost" of an item accounts for taxes and discounts.
        For example, a 5% discount applies to all items equally."""
        return round(self.price / receipt.item_subtotal() * receipt.grand_total, 2)

    def set_ynab_category(self, categories_map: dict[str, Category]):
        if self.category in categories_map:
            self._ynab_category = categories_map[self.category]
        self._ynab_category = None

    @property
    def ynab_category(self):
        return self._ynab_category


class Receipt(BaseModel):
    items: list[Item]
    total_before_tax: Decimal
    subtotal: Decimal
    grand_total: Decimal
    date: dt.date

    def item_subtotal(self):
        return sum(i.price for i in self.items)

    def set_ynab_category(self, categories: list[Category]):
        categories_map = {c.get_name(): c for c in categories}
        for item in self.items:
            item.set_ynab_category(categories_map)


class SaveSubTransaction(BaseModel):
    amount: int
    memo: str  # name of thing
    category_id: Optional[str]

    @classmethod
    def from_item(cls, receipt: Receipt, item: Item):
        return cls(
            amount=-abs(int(round(item.adjusted_cost(receipt) * 1000))),
            memo=item.short_name,
            category_id=item.ynab_category.category_id if item.ynab_category else None,
        )


class NewTransaction(BaseModel):
    account_id: str  # uuid
    date: dt.date
    amount: int
    payee_name: str
    memo: Optional[str]
    subtransactions: Optional[list[SaveSubTransaction]] = None
    category_id: Optional[str] = None

    @field_serializer("date")
    def serialize_dt(self, date: dt.date, *_, **__):
        return str(date)  # %Y-%m-%d

    @classmethod
    def from_receipt(
        cls, order_id: str, account_id: str, payee_name: str, receipt: Receipt
    ) -> "NewTransaction":
        if len(receipt.items) == 1:
            # Orders of exact 1 item should not be split into multiple transactions.
            item = receipt.items[0]
            return cls(
                account_id=account_id,
                date=receipt.date,
                amount=-abs(int(round(receipt.grand_total * 1000))),
                payee_name=payee_name,
                memo=f'{item.short_name} ({order_id})',
                category_id=item.ynab_category.category_id if item.ynab_category else None,
            )
        else:
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
