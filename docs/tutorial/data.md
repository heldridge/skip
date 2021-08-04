# Data

In addition to Markdown, Skip can render [Jinja2](https://jinja.palletsprojects.com/en/3.0.x/) template files.

Let's create a template to render. Any code block that starts with a comment represents a full file.

Create a file called `jinja.j2`:

``` jinja2
<!-- jinja2.j2 -->

<ul>
{% for i in [1, 2, 3] %}
    <li>{{ i }}</li>
{% endfor %}
</ul>
```

You can now check out the `_site` folder or go to [`localhost:8080/jinja/`](localhost:8080/jinja/) to see the rendered list

## Frontmatter

Skip supports Jeckyll-style frontmatter, where the start of any file can contain YAML data that becomes usable in the template.

Change the `jinja.j2` file to the following:

``` jinja2
<!-- jinja2.j2 -->
---
fruits:
  - apple
  - banana
  - pear
---

<ul>
{% for fruit in fruits %}
    <li>{{ fruit }}</li>
{% endfor %}
</ul>
```

Now check out the generated page and see the `fruits` data used in the template!

## 

Armed with the knowledge of data, you can now move on to [layouts](/tutorial/layouts/)