---
layout: single
title: מתכונים משפחתיים
permalink: /
classes: wide
---

<h1>מתכונים של הברהומים</h1>

<p>
ברוכים הבאים לאתר המתכונים המשפחתי.<br>
מתכונים ביתיים, ברורים ונוחים לבישול.
</p>

<hr>

<!-- סינון לפי קטגוריה -->
{% include recipe-filter.html %}


<h2>כל המתכונים</h2>

<div class="recipes-grid">
  {% assign sorted = site.recipes | sort: "title" %}
  {% for recipe in sorted %}
    <div class="recipe-card" data-category="{{ recipe.category }}">
      <a href="{{ recipe.url | relative_url }}" class="recipe-card-link">

        {% if recipe.image and recipe.image != "" %}
          <div class="recipe-card-image-wrapper">
            <img
              src="{{ recipe.image | relative_url }}"
              alt="{{ recipe.title }}"
              loading="lazy"
              class="recipe-card-image">
          </div>
        {% else %}
          <div class="recipe-card-image-wrapper empty"></div>
        {% endif %}

        <div class="recipe-card-body">
          <h3 class="recipe-card-title">{{ recipe.title }}</h3>

          {% if recipe.description %}
            <p class="recipe-card-desc">{{ recipe.description }}</p>
          {% endif %}
        </div>

      </a>
    </div>
  {% endfor %}
</div>

<script>
document.addEventListener('DOMContentLoaded', function () {
  const filter = document.getElementById('recipe-filter');
  if (!filter) return;

  filter.addEventListener('change', function () {
    const value = this.value;
    document.querySelectorAll('.recipe-card').forEach(card => {
      card.style.display =
        (value === 'all' || card.dataset.category === value) ? '' : 'none';
    });
  });
});
</script>
