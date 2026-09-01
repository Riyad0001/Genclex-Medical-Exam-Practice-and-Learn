from openai import OpenAI
from django.conf import settings
from bs4 import BeautifulSoup
import re

client = OpenAI(api_key=settings.OPENAI_API_KEY)


class AIFormatterService:

    @staticmethod
    def _strip_literal_newline_tokens(text):
        return re.sub(r"\\+n", "", text or "")

    @staticmethod
    def _looks_like_html(text):
        return bool(re.search(r"<[a-zA-Z][\s\S]*?>", text))

    @staticmethod
    def _plain_text_to_html(text):
        paragraphs = [paragraph.strip() for paragraph in re.split(r"\n\s*\n+", text) if paragraph.strip()]

        if not paragraphs:
            return ""

        blocks = []

        for paragraph in paragraphs:
            lines = [line.strip() for line in paragraph.split("\n") if line.strip()]

            if lines:
                blocks.append(f"<p>{'<br>'.join(lines)}</p>")

        return "\n".join(blocks)

    @staticmethod
    def _normalize_html_output(html):
        normalized = (html or "").replace("\r\n", "\n").strip()
        normalized = AIFormatterService._strip_literal_newline_tokens(normalized)

        if not normalized:
            return ""

        soup = BeautifulSoup(normalized, "lxml")
        body = soup.body

        for node in soup.find_all(string=True):
            text = AIFormatterService._strip_literal_newline_tokens(str(node))
            text = re.sub(r"\s{2,}", " ", text).strip()

            if text:
                node.replace_with(text)
            else:
                node.extract()

        if body is not None:
            cleaned = body.decode_contents()
        else:
            cleaned = soup.decode()

        cleaned = cleaned.replace("\r\n", "\n").strip()
        cleaned = AIFormatterService._strip_literal_newline_tokens(cleaned)
        cleaned = re.sub(r"\\+n", "", cleaned)
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
        cleaned = re.sub(r">\s+<", "><", cleaned)
        cleaned = re.sub(r"[\t ]{2,}", " ", cleaned)

        return cleaned.strip()

    @staticmethod
    def format_html(html):

        html = (html or "").replace("\r\n", "\n").strip()

        if not html:
            return ""

        if not AIFormatterService._looks_like_html(html):
            html = AIFormatterService._plain_text_to_html(html)

        print("\n" + "=" * 80)
        print("ORIGINAL HTML")
        print("=" * 80)
        print(html)

        system_prompt = """
You are an expert HTML note formatter.

Your task is to improve HTML lecture notes while preserving all information.

STRICT RULES:

- Return ONLY valid HTML.
- Do NOT return Markdown.
- Do NOT wrap the response inside ```html```.
- Preserve existing HTML whenever possible.
- Preserve all existing styles, colors, font sizes, and alignment.
- Preserve images, links, and tables.
- Never remove information.
- Never invent information.
- Correct grammar and spelling.
- Improve readability.
- Break long paragraphs.
- Add headings where appropriate.
- Convert suitable paragraphs into bullet points.
- Convert processes into numbered lists.
- Make important keywords bold using <strong>.
- Underline important definitions using <u>.
- Highlight formulas using <mark>.
- Use colored spans only for important concepts.

Example:

<span style="color:#d32f2f;"><strong>Important</strong></span>

Allowed tags:

h1,h2,h3,h4,p,strong,em,u,mark,
ul,ol,li,
table,thead,tbody,tr,th,td,
blockquote,
div,span,br,hr,img,a

Return ONLY HTML.
"""

        prompt = f"""
Please professionally format the following HTML lecture note.

Requirements:

1. Keep all existing content.
2. Improve grammar.
3. Improve formatting.
4. Preserve existing HTML formatting.
5. Add formatting only where it improves readability.
6. Return ONLY valid HTML.

HTML:

{html}
"""

        print("\n" + "=" * 80)
        print("PROMPT")
        print("=" * 80)
        print(prompt)

        response = client.chat.completions.create(
            model="gpt-4.1",
            temperature=0.3,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
        )

        result = response.choices[0].message.content.strip()

        # Remove markdown fences if returned
        result = re.sub(r"^```html\s*", "", result, flags=re.IGNORECASE)
        result = re.sub(r"^```\s*", "", result)
        result = re.sub(r"\s*```$", "", result)

        result = AIFormatterService._normalize_html_output(result)

        print("\n" + "=" * 80)
        print("GPT OUTPUT")
        print("=" * 80)
        print(result)

        return result