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

    {% case top_group %}
      {% when "חומרי גלם" %}
        {% assign group_description = "רכיבי בסיס שחוזרים במתכונים ודורשים בחירה, השריה, הכנה או שימוש נכון." %}
      {% when "תבלינים ותערובות" %}
        {% assign group_description = "תבלינים ותערובות שמגדירים טעם, ריח וזהות משפחתית במנות." %}
      {% when "רטבים וממרחים" %}
        {% assign group_description = "רטבים, ממרחים ותוספות שמחברים בין מתכונים ומשנים את האופי של המנה." %}
      {% when "כבישה ותסיסה" %}
        {% assign group_description = "רכיבים ותהליכים שבהם זמן, מלח, חומציות או תרבית יוצרים טעם ומרקם." %}
      {% when "טכניקות ובסיסים" %}
        {% assign group_description = "הכנות, שלבים ועקרונות עבודה שמשפיעים על עומק הטעם והצלחת המתכון." %}
      {% when "בשר, דגים ונתחים" %}
        {% assign group_description = "חומרי גלם מן החי, נתחים וסוגי הכנה שחשוב להבין לפני הבישול." %}
      {% when "כלים ומכשירים" %}
        {% assign group_description = "כלים, מכשירים ושיטות עבודה שמופיעים סביב המתכונים או ישמשו הרחבות עתידיות." %}
      {% when "עקרונות בישול" %}
        {% assign group_description = "עקרונות כלליים שעוזרים להבין למה מתכון עובד ולא רק איך לבצע אותו." %}
      {% when "אחר" %}
        {% assign group_description = "פריטים שעדיין לא שויכו לקבוצת ידע קבועה ודורשים מיון עתידי." %}
      {% else %}
        {% assign group_description = "" %}
    {% endcase %}

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

        {% if group_description %}
          <p class="ingredients-group-description">{{ group_description }}</p>
        {% endif %}

        <div>
          {{ group_cards }}
        </div>
      </section>
    {% endif %}
  {% endfor %}
</div>
