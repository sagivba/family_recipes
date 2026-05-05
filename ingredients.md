---
layout: default
title: מזווה הידע
permalink: /ingredients/
---

<div class="ingredients-index" dir="rtl">
  <h1>{{ page.title }}</h1>
  <p>חומרי גלם, תבלינים, טכניקות, תסיסות, נתחים, כלים ועקרונות בישול שמופיעים סביב המתכונים המשפחתיים.</p>

  {% assign ingredients_sorted = site.ingredients | sort: "title" %}
  {% assign top_groups = "חומרי גלם|תבלינים ותערובות|רטבים וממרחים|כבישה ותסיסה|טכניקות ובסיסים|בשר, דגים ונתחים|כלים ומכשירים|עקרונות בישול|אחר" | split: "|" %}

  {% for top_group in top_groups %}
    {% capture group_cards %}{% endcapture %}
    {% assign group_count = 0 %}

    {% for ingredient in ingredients_sorted %}
      {% assign category = ingredient.category | default: "" | strip %}
      {% assign title_text = ingredient.title | default: "" %}
      {% assign title_down = title_text | downcase %}
      {% assign url_down = ingredient.url | downcase %}
      {% assign mapped_group = "אחר" %}

      {% case category %}
        {% when "קטניות" or "מחית / בסיס" or "חומר גלם דורש טיפול" or "שומן מתובל / מחמצת מתוקה" %}
          {% assign mapped_group = "חומרי גלם" %}
        {% when "תבלין ארומטי" or "תערובת תבלינים" %}
          {% assign mapped_group = "תבלינים ותערובות" %}
        {% when "רוטב חריף" or "רוטב חי" %}
          {% assign mapped_group = "רטבים וממרחים" %}
        {% when "כבושים" or "תסיסה וכבישה" or "תהליך תסיסה" or "תרבית חיה" or "דגים כבושים" %}
          {% assign mapped_group = "כבישה ותסיסה" %}
        {% when "רכיב ביניים / טכניקה" or "רכיב ביניים / טכניקת עומק" %}
          {% assign mapped_group = "טכניקות ובסיסים" %}
        {% when "בסיס מסורתי" %}
          {% assign mapped_group = "טכניקות ובסיסים" %}
        {% when "בשר טחון" %}
          {% assign mapped_group = "בשר, דגים ונתחים" %}
      {% endcase %}

      {% if mapped_group == "אחר" %}
        {% if category contains "כלים" or category contains "מכשיר" or title_text contains "סכין" or title_text contains "מחבת" or title_text contains "סיר" or title_text contains "טאבון" or url_down contains "knife" or url_down contains "tool" %}
          {% assign mapped_group = "כלים ומכשירים" %}
        {% elsif category contains "עקרונות" or category contains "עיקרון" or title_text contains "עיקרון" or title_text contains "יסודות" or url_down contains "principle" %}
          {% assign mapped_group = "עקרונות בישול" %}
        {% elsif category contains "ירק חריף" or category contains "רכיב טעם" or category contains "שומן מתובל" %}
          {% assign mapped_group = "חומרי גלם" %}
        {% elsif category contains "נתח" or category contains "בקר" or category contains "בשר" or category contains "דגים" or title_text contains "נתח" or title_text contains "בקר" or title_text contains "בשר" or title_text contains "דג" or title_text contains "כבש" or title_text contains "עוף" or url_down contains "beef" or url_down contains "meat" or url_down contains "fish" %}
          {% assign mapped_group = "בשר, דגים ונתחים" %}
        {% endif %}
      {% endif %}

      {% if mapped_group == top_group %}
        {% capture group_cards %}
          {{ group_cards }}
          <article class="ingredient-card">
            <h3><a href="{{ ingredient.url | relative_url }}">{{ ingredient.title }}</a></h3>
            {% if ingredient.category %}<p>{{ ingredient.category }}</p>{% endif %}
            {% if ingredient.origin %}<p>{{ ingredient.origin }}</p>{% endif %}
          </article>
        {% endcapture %}
        {% assign group_count = group_count | plus: 1 %}
      {% endif %}
    {% endfor %}

    {% if group_count > 0 %}
      <section class="ingredients-group">
        <h2>{{ top_group }}</h2>
        <div>
          {{ group_cards }}
        </div>
      </section>
    {% endif %}
  {% endfor %}
</div>
