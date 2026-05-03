---
layout: default
title: מאגר מרכיבים
permalink: /ingredients/
---

<div class="ingredients-index" dir="rtl">
  <h1>{{ page.title }}</h1>

  {% assign ingredients_sorted = site.ingredients | sort: "title" %}
  {% assign grouped = ingredients_sorted | group_by: "category" %}

  {% for group in grouped %}
    <section class="ingredients-group">
      <h2>{% if group.name and group.name != "" %}{{ group.name }}{% else %}ללא קטגוריה{% endif %}</h2>
      <div>
        {% for ingredient in group.items %}
          <article class="ingredient-card">
            <h3><a href="{{ ingredient.url | relative_url }}">{{ ingredient.title }}</a></h3>
            {% if ingredient.origin %}<p>{{ ingredient.origin }}</p>{% endif %}
          </article>
        {% endfor %}
      </div>
    </section>
  {% endfor %}
</div>
