from typing import List, Optional
import logging


class LLMRecipeRewriter:
    """
    Rewrite recipe markdown using an LLM.

    Responsibilities:
    - Build prompts (normalize / fix)
    - Call LLM client
    - Return FULL markdown text

    This class does NOT:
    - Validate output
    - Touch filesystem
    """

    def __init__(self, client, model: str, logger: logging.Logger | None = None):
        self.client = client
        self.model = model
        self.logger = logger

    # -------------------------
    # prompt builders
    # -------------------------

    def _build_normalize_prompt(self, markdown: str) -> str:
        return f"""
    You are a professional recipe editor.

    Rules (MANDATORY):
    - Output the FULL markdown document only.
    - DO NOT wrap the output in code blocks (no ``` or ```yaml).
    - The YAML front matter MUST:
      - Start at the very first line of the file
      - Be wrapped with '---' at the beginning and end
      - Be valid YAML
    - Do not invent ingredients or preparation steps.
    - Preserve the original meaning.
    - Use Hebrew.

    Required structure (exact order):
    1. YAML front matter (--- at top and bottom)
    2. ## מצרכים
    3. ## אופן ההכנה
    4. ## ערכים תזונתיים (הערכה ל-100 גרם)
    5. ### ויטמינים ומינרלים בולטים
    6. ## הערות

    Input:
    {markdown}
    """.strip()

    def _build_fix_prompt(self, markdown: str, issues: List[str]) -> str:
        issues_block = "\n".join(f"- {issue}" for issue in issues)

        return f"""
The following recipe markdown failed validation.

Issues:
{issues_block}

Rules:
- Fix ONLY the listed issues.
- Do not change meaning.
- Do not invent new content.
- Output FULL corrected markdown only.

Input:
{markdown}
""".strip()

    # -------------------------
    # public API
    # -------------------------

    def rewrite(
        self,
        markdown: str,
        issues: Optional[List[str]] = None,
        attempt: int = 1,
    ) -> str:
        """
        Rewrite or fix recipe markdown.

        :param markdown: Original markdown text
        :param issues: Optional list of lint issues (for fix mode)
        :param attempt: Attempt number (for logging only)
        :return: Rewritten markdown
        """

        if issues:
            prompt = self._build_fix_prompt(markdown, issues)
            mode = "fix"
        else:
            prompt = self._build_normalize_prompt(markdown)
            mode = "normalize"

        if self.logger:
            self.logger.info(
                "LLM rewrite mode=%s attempt=%d chars=%d",
                mode,
                attempt,
                len(markdown),
            )

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            temperature=0.2,
        )

        content = response.choices[0].message.content

        if self.logger:
            self.logger.debug(
                "LLM output received chars=%d",
                len(content) if content else 0,
            )

        return content
