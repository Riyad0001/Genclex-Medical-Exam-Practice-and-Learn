import anthropic
from django.conf import settings


client = anthropic.Anthropic(
    api_key=settings.ANTHROPIC_API_KEY
)


def generate_claude_response(prompt):
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=4000,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response.content[0].text


import anthropic
from django.conf import settings


client = anthropic.Anthropic(
    api_key=settings.ANTHROPIC_API_KEY
)


def generate_claude_response(prompt):
    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=4000,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response.content[0].text


