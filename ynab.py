import os
import requests
from models import NewTransaction, Category


BUDGET_ID = 'last-used'
YNAB_API_KEY = os.environ['YNAB_API_KEY']
DEFAULT_HEADERS = {
    'accept': 'application/json',
    'Authorization': f'Bearer {YNAB_API_KEY}',
    'Content-Type': 'application/json',
}


def get_accounts() -> list[any]:
    """Used to get your account ids for setup purposes"""
    resp = requests.get(
        f'https://api.ynab.com/v1/budgets/{BUDGET_ID}/accounts',
        headers=DEFAULT_HEADERS,
    )
    resp.raise_for_status()
    return resp.json()['data']

def post_transaction(transaction: NewTransaction) -> list[str]:
    resp = requests.post(
        f'https://api.ynab.com/v1/budgets/{BUDGET_ID}/transactions',
        headers=DEFAULT_HEADERS,
        json=dict(transaction=transaction.model_dump()),
    )
    resp.raise_for_status()
    return resp.json()['data']['transaction_ids']


def get_categories() -> list[Category]:
    resp = requests.get(
        f'https://api.ynab.com/v1/budgets/{BUDGET_ID}/categories',
        headers=DEFAULT_HEADERS,
    )
    resp.raise_for_status()
    categories_data = resp.json()
    return [
        Category(cg['name'], c['name'], c['id'])
        for cg in categories_data['data']['category_groups']
        for c in cg['categories']
        if cg['name'].startswith('[Auto]')
    ]
