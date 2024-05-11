import datetime as dt
import argparse
import logging
import os
from contextlib import closing
import re

from bs4 import BeautifulSoup
from tqdm import tqdm

import db
import gpt
import ynab
from models import Receipt, NewTransaction


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    filemode="w",
)


def _receipt_html_to_txt(html: str):
    soup = BeautifulSoup(html, features="html.parser")
    return re.sub("\n\s+", "\n", soup.text)


def main(account_id: str, input_path: str, db_path: str, categorize: bool):
    with closing(db.RunStore(db_path)) as store:
        unprocessed_orders = [
            order_id
            for order_id in os.listdir(input_path)
            if not store.has_amazon_order(order_id)
        ]

        categories = []
        if categorize:
            categories = ynab.get_categories()

        for order_id in tqdm(unprocessed_orders):
            try:
                logging.info(f"Processing order: {order_id}")
                with open(os.path.join(input_path, order_id), "r") as f:
                    receipt_text = _receipt_html_to_txt(f.read())

                other = "other"
                receipt_json = gpt.chatgpt(
                    receipt_text, [c.get_name() for c in categories] + [other]
                )
                receipt = Receipt.model_validate(receipt_json)
                receipt.set_ynab_category(categories)
                if receipt.grand_total != 0:
                    logging.info(f"Valid Receipt, uploading to YNAB")
                    transaction = NewTransaction.from_receipt(
                        order_id, account_id, "Amazon", receipt
                    )
                    ynab_id, *_ = ynab.post_transaction(transaction)
                else:
                    logging.info(f"Empty receipt. Skipping import")
                    ynab_id = ""
                store.add_amazon_order(
                    ynab_id,
                    order_id,
                    receipt.date,
                    float(receipt.subtotal),
                    float(receipt.grand_total),
                )
            except Exception as e:
                logging.error(f"Order ID {order_id} Failed: {str(e)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Process a directory full of Amazon reciepts, and upload them to YNAB."
    )

    parser.add_argument(
        "-a",
        "--account_id",
        type=str,
        help="YNAB Account ID that made the Amazon purchases.",
    )

    parser.add_argument(
        "-i", "--input_path", type=str, help="Directory of receipts folder"
    )

    parser.add_argument(
        "-db",
        "--db_path",
        type=str,
        help="Path to SQLite DB that stores data in-between runs",
    )

    parser.add_argument(
        "-c",
        "--categorize",
        type=bool,
        help="Attempt to categorize the transaction?",
        default=False,
    )

    main(**dict(vars(parser.parse_args())))
