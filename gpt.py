import json
from openai import OpenAI


client = OpenAI()

usage_completion_tokens = 0
usage_prompt_tokens = 0
usage_total_tokens = 0


prompt = """\
You are a helpful assistant designed to read Amazon receipts and summarize the output in JSON.
The output must fit the following schema: {"grand_total": "decimal", "subtotal": "decimal", "total_before_tax": "decimal", "date": "YYYY-MM-DD", "items": [{"short_name": "string", "title": "string", "price": "decimal"}]
"""


def chatgpt(receipt: str):
    global usage_completion_tokens, usage_prompt_tokens, usage_total_tokens
    response = client.chat.completions.create(
        model="gpt-3.5-turbo-0125",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": receipt},
        ],
    )
    usage_completion_tokens += response.usage.completion_tokens
    usage_prompt_tokens += response.usage.prompt_tokens
    usage_total_tokens += response.usage.total_tokens
    return json.loads(response.choices[0].message.content)
