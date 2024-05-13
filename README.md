# YNAB_AMAZON - Upload your Amazon Receipts.
This repo takes your HTML Amazon receipts, parses them with ChatGPT, and uploads them to YNAB as split transactions. It's intended to be used in combination with the [Amazon Orders WebScrapper](https://github.com/aelzeiny/Amazon-Orders-WebScraper), which will do the actual receipt scrapping.

### Example:
**Note**: Transactions with multiple items are automatically split into multiple sub-transactions, as shown below.
![YNAB Amazon imported screenshot](./docs/YNAB_AMAZON.png)

### Example Usage:
```
python main.py -a account_uuid -i ./receipts -db .db.sqlite
```

### Why?
* The wonderful minds behind the **AWS CLOUD** cannot provide an OAuth API 🙃
* Amazon is mostly server-side generated, and AFAIK there's no direct API call that can grab these details.
* Amazon killed the "download orders as CSV" feature.

### Auto-categorization
The `-c true` flag will attempt to auto-categorize transactions for you based on category groups that start with "[auto]". By default this behavior is turned off.