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
        <div>
          {{ group_cards }}
        </div>
      </section>
    {% endif %}
  {% endfor %}
</div>
