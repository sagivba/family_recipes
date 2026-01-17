---
layout: single
title: מתכונים משפחתיים
permalink: /
classes: wide
---

ברוכים הבאים לאתר המתכונים המשפחתי.  
מתכונים ביתיים, ברורים ונוחים לבישול.

---

## כל המתכונים

<div class="recipes-grid">

{% assign sorted = site.recipes | sort: "title" %}
{% for recipe in sorted %}
  <div class="recipe-card">
    <a href="{{ recipe.url | relative_url }}">
      <h3>{{ recipe.title }}</h3>
      {% if recipe.description %}
        <p class="recipe-card-desc">{{ recipe.description }}</p>
      {% endif %}
    </a>
  </div>
{% endfor %}

</div>
