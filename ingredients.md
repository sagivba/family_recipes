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
    {% assign seen_urls = "|" %}

    {% for ingredient in ingredients_sorted %}
      {% assign category = ingredient.category | default: "" | strip %}

      {% if top_groups contains category %}
        {% assign effective_group = category %}
      {% else %}
        {% assign effective_group = "אחר" %}
      {% endif %}

      {% assign unique_key = "|" | append: ingredient.url | append: "|" %}

      {% if effective_group == top_group %}
        {% unless seen_urls contains unique_key %}
          {% capture group_cards %}
            {{ group_cards }}
            <article class="ingredient-card">
              <h3>
                <a href="{{ ingredient.url | relative_url }}">{{ ingredient.title }}</a>
              </h3>

              {% if ingredient.subcategory %}
                <p>{{ ingredient.subcategory }}</p>
              {% endif %}

              {% if ingredient.origin %}
                <p>{{ ingredient.origin }}</p>
              {% endif %}
            </article>
          {% endcapture %}

          {% assign seen_urls = seen_urls | append: ingredient.url | append: "|" %}
          {% assign group_count = group_count | plus: 1 %}
        {% endunless %}
      {% endif %}
    {% endfor %}

    {% if group_count > 0 %}
      <section class="ingredients-group">
        <h2>{{ top_group }}</h2>

        {% if top_group == "חומרי גלם" %}
          <p class="ingredients-group-description">רכיבי בסיס שחוזרים במתכונים ודורשים בחירה, השריה, הכנה או שימוש נכון.</p>
        {% elsif top_group == "תבלינים ותערובות" %}
          <p class="ingredients-group-description">תבלינים ותערובות שמגדירים טעם, ריח וזהות משפחתית במנות.</p>
        {% elsif top_group == "רטבים וממרחים" %}
          <p class="ingredients-group-description">רטבים, ממרחים ותוספות שמחברים בין מתכונים ומשנים את האופי של המנה.</p>
        {% elsif top_group == "כבישה ותסיסה" %}
          <p class="ingredients-group-description">רכיבים ותהליכים שבהם זמן, מלח, חומציות או תרבית יוצרים טעם ומרקם.</p>
        {% elsif top_group == "טכניקות ובסיסים" %}
          <p class="ingredients-group-description">הכנות, שלבים ועקרונות עבודה שמשפיעים על עומק הטעם והצלחת המתכון.</p>
        {% elsif top_group == "בשר, דגים ונתחים" %}
          <p class="ingredients-group-description">חומרי גלם מן החי, נתחים וסוגי הכנה שחשוב להבין לפני הבישול.</p>
        {% elsif top_group == "כלים ומכשירים" %}
          <p class="ingredients-group-description">כלים, מכשירים ושיטות עבודה שמופיעים סביב המתכונים או ישמשו הרחבות עתידיות.</p>
        {% elsif top_group == "עקרונות בישול" %}
          <p class="ingredients-group-description">עקרונות כלליים שעוזרים להבין למה מתכון עובד ולא רק איך לבצע אותו.</p>
        {% elsif top_group == "אחר" %}
          <p class="ingredients-group-description">פריטים שעדיין לא שויכו לקבוצת ידע קבועה ודורשים מיון עתידי.</p>
        {% endif %}

        <div>
          {{ group_cards }}
        </div>
      </section>
    {% endif %}
  {% endfor %}
</div>
