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
      {% assign url_down = ingredient.url | downcase %}
      {% assign mapped_group = "אחר" %}

      {% if category == "קטניות" or category == "מחית / בסיס" or category == "חומר גלם דורש טיפול" or category == "שומן מתובל / מחמצת מתוקה" %}
        {% assign mapped_group = "חומרי גלם" %}
      {% elsif category == "תבלין ארומטי" or category == "תערובת תבלינים" %}
        {% assign mapped_group = "תבלינים ותערובות" %}
      {% elsif category == "רוטב חריף" or category == "רוטב חי" %}
        {% assign mapped_group = "רטבים וממרחים" %}
      {% elsif category == "כבושים" or category == "תסיסה וכבישה" or category == "תהליך תסיסה" or category == "תרבית חיה" or category == "דגים כבושים" %}
        {% assign mapped_group = "כבישה ותסיסה" %}
      {% elsif category == "רכיב ביניים / טכניקה" or category == "רכיב ביניים / טכניקת עומק" or category == "בסיס מסורתי" %}
        {% assign mapped_group = "טכניקות ובסיסים" %}
      {% elsif category == "בשר טחון" %}
        {% assign mapped_group = "בשר, דגים ונתחים" %}
      {% elsif category contains "ירק חריף" or category contains "רכיב טעם" or category contains "שומן מתובל" %}
        {% assign mapped_group = "חומרי גלם" %}
      {% elsif category contains "כלים" or category contains "מכשיר" or title_text contains "סכין" or title_text contains "מחבת" or title_text contains "סיר" or title_text contains "טאבון" or url_down contains "knife" or url_down contains "tool" %}
        {% assign mapped_group = "כלים ומכשירים" %}
      {% elsif category contains "עקרונות" or category contains "עיקרון" or title_text contains "עיקרון" or title_text contains "יסודות" or url_down contains "principle" %}
        {% assign mapped_group = "עקרונות בישול" %}
      {% elsif category contains "נתח" or category contains "בקר" or category contains "בשר" or category contains "דגים" or title_text contains "נתח" or title_text contains "בקר" or title_text contains "בשר" or title_text contains "דג" or title_text contains "כבש" or title_text contains "עוף" or url_down contains "beef" or url_down contains "meat" or url_down contains "fish" %}
        {% assign mapped_group = "בשר, דגים ונתחים" %}
      {% endif %}

      {% if mapped_group == top_group %}
        {% capture group_cards %}
          {{ group_cards }}
          <article class="ingredient-card">
            <h3>
              <a href="{{ ingredient.url | relative_url }}">{{ ingredient.title }}</a>
            </h3>

            {% if ingredient.category %}
              <p>{{ ingredient.category }}</p>
            {% endif %}

            {% if ingredient.origin %}
              <p>{{ ingredient.origin }}</p>
            {% endif %}
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
