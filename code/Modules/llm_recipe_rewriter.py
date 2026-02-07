from typing import List, Optional
from Modules.config import Config
normalise_prompt="""
 You are a professional recipe editor.

        MANDATORY RULES:
        - Output the FULL markdown document only.
        - DO NOT wrap the output in code blocks (no ``` or ```markdown).
        - The YAML front matter MUST start at the very first line of the file.
        - The YAML front matter MUST be wrapped with '---' at the beginning and end.
        - The YAML front matter MUST be valid YAML.

        The YAML front matter MUST include ALL of the following fields
        (even if the value is unknown or empty):

        layout: recipe
        title
        category
        type
        origin
        spiciness
        diabetic_friendly
        image
        source
        notes
        description

        GENERAL FIELD RULES:
        - If a value is missing or unknown, use an empty string ("").
        - Do NOT invent facts or external information.
        - Do NOT use knowledge that is not present or clearly implied by the recipe.
        - Do NOT translate values unless they already exist in Hebrew.
        - Preserve existing values exactly if present.
        - Use Hebrew only.

        SPECIAL RULES FOR spiciness:
        - The field "spiciness" represents dominant flavor profile, NOT heat level.
        - You MAY infer a reasonable value based ONLY on ingredients and preparation.
        - Allowed values include (examples, not exhaustive):
          מלוח, מתוק, מתוק מלוח, חריף, פיקנטי, ללא
        - You MAY combine values if appropriate (e.g. "מתוק מלוח").
        - Do NOT invent exotic, creative, or uncommon flavor descriptions.
        - If no reasonable inference can be made, use empty string ("").

        SPECIAL RULES FOR diabetic_friendly:
        - The field "diabetic_friendly" indicates suitability for people with diabetes.
        - Allowed values are: "כן", "לא", or empty string ("").
        - You MAY infer this field based ONLY on ingredients and preparation method.
        - Do NOT perform numeric nutritional calculations.
        - Do NOT estimate grams, calories, or glycemic index numerically.

        Set diabetic_friendly to "כן" ONLY IF ALL of the following apply:
        - No added sugar (e.g. sugar, honey, syrup, dates, jam).
        - No refined carbohydrates (e.g. flour, bread, pasta, rice, potatoes).
        - Carbohydrates, if present, come mainly from vegetables or legumes.
        - The recipe includes a clear protein source and/or fat accompanying carbohydrates.

        Set diabetic_friendly to "לא" IF ANY of the following apply:
        - Added sugar is present.
        - Refined carbohydrates are present.
        - The recipe is primarily a sweet dish.

        If the information is insufficient or unclear, use empty string ("").

        CONTENT RULES:
        - Do NOT invent ingredients or preparation steps.
        - Preserve the original meaning and quantities.
        - Do NOT add explanations or editorial text.

        REQUIRED STRUCTURE (exact order, no extra sections):
        1. YAML front matter (--- at top and bottom)
        2. ## מצרכים
        3. ## אופן ההכנה
        4. ## ערכים תזונתיים (הערכה ל-100 גרם)
        5. ### ויטמינים ומינרלים בולטים
        6. ## הערות

        STRICTLY FORBIDDEN:
        - Adding new sections
        - Adding commentary or explanations - except for "ערכים תזונתיים (הערכה ל-100 גרם)" and "ויטמינים ומינרלים בולטים" if they are missing, in which case you may add them with empty content.
        - Adding markdown fences
        - Returning partial documents
"""

class LLMRecipeRewriter:
    """
    Rewrite recipe markdown using an LLM.
    Ensures clean markdown output suitable for publication.
    """


    def __init__(self, client, model, logger=None):
        self.client = client
        self.model = model
        self.logger = logger

    @staticmethod
    def strip_markdown_code_fence(text: str, logger=None) -> str:
        """
        Remove wrapping markdown code fences (``` or ```markdown) if present.
        """
        stripped = text.strip()
        lines = stripped.splitlines()
        if len(lines) >= 2:
            first = lines[0].strip()
            last = lines[-1].strip()
            if first.startswith("```") and last == "```":
                if logger:
                    logger.info("LLM output wrapped in markdown code fence – stripping it")
                return "\n".join(lines[1:-1]).strip()
        return stripped

    def _build_normalize_prompt(self, markdown: str) -> str:
        """
        Build the normalization prompt sent to the LLM.

        The goal is to:
        - Ensure a complete and valid YAML front matter with ALL required fields
        - Normalize structure and headers order
        - Preserve meaning and existing content
        - Avoid code fences or any extra wrapping
        """

        return f"""
        {normalise_prompt}

        Input recipe markdown:
        {markdown}
        """.strip()

    def _build_fix_prompt(self, markdown: str, issues: List[str]) -> str:
        return f"""
The following recipe markdown failed validation.

Issues:
{chr(10).join(f"- {i}" for i in issues)}

Rules:
- Fix ONLY the listed issues.
- Do not change meaning.
- Do not invent new content.
- Output FULL corrected markdown only.
- DO NOT wrap the output in code blocks.

Input:
{markdown}
""".strip()

    def _build_frontmatter_enrichment_prompt(self, markdown: str) -> str:
        return f"""
        You are a professional recipe metadata editor.

        TASK:
        Enrich ONLY the YAML front matter of the recipe below.

        RULES (MANDATORY):
        - Output the FULL markdown document.
        - DO NOT wrap output in code blocks.
        - Do NOT change recipe body sections in any way.
        - Do NOT invent facts or external information.
        - Extract or infer information ONLY from the recipe content.
        - If a value cannot be inferred, use empty string ("").
        - Preserve existing front matter values exactly if present.
        - Use Hebrew only.

        The YAML front matter MUST include exactly these fields:

        layout: recipe
        title
        category
        type
        origin
        spiciness
        diabetic_friendly
        image
        source
        notes
        description

        SPECIAL RULES FOR spiciness:
        - The field "spiciness" represents dominant flavor profile, NOT heat level.
        - You MAY infer a reasonable value based ONLY on ingredients and preparation.
        - Allowed values include (examples, not exhaustive):
          מלוח, מתוק, מתוק מלוח, חריף, פיקנטי, ללא
        - You MAY combine values if appropriate (e.g. "מתוק מלוח").
        - Do NOT invent exotic, creative, or uncommon flavor descriptions.
        - If no reasonable inference can be made, use empty string ("").

        SPECIAL RULES FOR diabetic_friendly:
        - The field "diabetic_friendly" indicates suitability for people with diabetes.
        - Allowed values are: "כן", "לא", or empty string ("").
        - You MAY infer this field based ONLY on ingredients and preparation method.
        - Do NOT perform numeric nutritional calculations.
        - Do NOT estimate grams, calories, or glycemic index numerically.

        Set diabetic_friendly to "כן" ONLY IF ALL of the following apply:
        - No added sugar (e.g. sugar, honey, syrup, dates, jam).
        - No refined carbohydrates (e.g. flour, bread, pasta, rice, potatoes).
        - Carbohydrates, if present, come mainly from vegetables or legumes.
        - The recipe includes a clear protein source and/or fat accompanying carbohydrates.

        Set diabetic_friendly to "לא" IF ANY of the following apply:
        - Added sugar is present.
        - Refined carbohydrates are present.
        - The recipe is primarily a sweet dish.

        If the information is insufficient or unclear, use empty string ("").

        STRICTLY FORBIDDEN:
        - Modifying recipe body content
        - Adding new fields
        - Adding explanations or commentary
        - Adding markdown fences
        - Returning partial documents

        Input recipe markdown:
        {markdown}
        """.strip()

    def _build_nutrition_enrichment_prompt(self, markdown: str) -> str:
        return f"""
You are a culinary nutrition estimator.

TASK:
Return ONLY the Markdown content that should be inserted
UNDER the following existing sections in the document:

## ערכים תזונתיים (הערכה ל-100 גרם)
### ויטמינים ומינרלים בולטים

IMPORTANT:
- Do NOT return the full document.
- Do NOT return YAML.
- Do NOT return ingredients or preparation steps.
- Return ONLY the content for these sections.

NUMERIC NUTRITION RULES (CRITICAL):
- ALWAYS return numeric values for:
  calories, carbohydrates, sugars, protein, fat, fiber.
- If ingredient weights are missing:
  assume standard household ingredient weights.
- If fat content is unknown:
  assume standard full-fat versions.
- Leaving the nutrition values section empty is FORBIDDEN.


FORMAT:
- Use bullet lists.
- Use units (קק"ל, גרם, מ"ג, מיקרוגרם).
- Use rounded values (no excessive precision).

VITAMINS & MINERALS:
- Return numeric values where commonly known.
- Otherwise, list without numbers.

FORBIDDEN:
- Medical advice
- Recommendations
- Disclaimers or explanations
- Any text outside the two sections

Input recipe markdown:
{markdown}
""".strip()



    def rewrite(
        self,
        markdown: str,
        issues: Optional[List[str]] = None,
        attempt: int = 1,
    ) -> str:
        """
        Rewrite or fix recipe markdown using the configured LLM.
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
                mode, attempt, len(markdown)
            )

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )

        content = response.choices[0].message.content or ""

        cleaned = self.strip_markdown_code_fence(content, self.logger)

        if self.logger:
            self.logger.debug("LLM output received chars=%d", len(cleaned))

        return cleaned
    def _call_llm(self, prompt: str) -> str:
        """
        Internal helper to call the LLM with a single prompt
        and return cleaned markdown output.
        """

        if self.logger:
            self.logger.info(
                "LLM call (frontmatter enrichment) chars=%d",
                len(prompt)
            )

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )

        content = response.choices[0].message.content or ""

        cleaned = self.strip_markdown_code_fence(content, self.logger)

        if self.logger:
            self.logger.debug(
                "LLM frontmatter enrichment output chars=%d",
                len(cleaned)
            )

        return cleaned

    def enrich_frontmatter(self, markdown: str) -> str:
        """
        Enrich YAML front matter using a dedicated AI prompt.
        This method ONLY fills front-matter fields and does not
        touch body content.
        """
        prompt = self._build_frontmatter_enrichment_prompt(markdown)
        return self._call_llm(prompt)

    def enrich_nutrition(self, markdown: str) -> str:
        """
        Generate ONLY the nutritional markdown block (lists allowed).
        This method MUST NOT return a full document.
        """
        prompt = self._build_nutrition_enrichment_prompt(markdown)
        nutrition_block = self._call_llm(prompt)

        # safety: never allow full documents here
        if nutrition_block.lstrip().startswith("---"):
            raise RuntimeError("Nutrition enrichment returned full document")

        return nutrition_block.strip()
