---
title: Data
date: "2021-01-03"
---
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

## Data Files

Skip also lets you specify data in files so that it can be used by multiple pages.

Create a `data` directory at the top level of your project:

``` bash
>>> mkdir data
```

Any data in this directory will be added to the `data` attribute for all the pages in your project.

Create a file in the data directory called `vegetables.json`:

``` json
{
  "vegetables": ["broccoli", "squash", "carrot"]
}
```

Now, change the `jinja.j2` file to the following:

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

<ul>
{% for vegetable in data.vegetables %}
    <li>{{ vegetable }}</li>
{% endfor %}
</ul>
```

Now you have both lists!

### Python Data Files

You can also use Python files as data files.
To do so, add a `get_data()` function to the file.

Rename `vegetables.json` to `vegetables.py`:

``` bash
>>> mv vegetables.json vegetables.py
```

And replace its content with the following

``` python
# data/vegetables.py

def get_data():
    return ["broccoli", "squash", "carrot"]
```

If you generate the site again, it will work just the same.

### Local Data Files

The data from any file in the special `data` directory will available on all the pages in your project.
Data from files in subfolders is only available to files in those folders and files that are further nested.

For example, if your project looks like this:

``` txt
my-project
  - data
    - global-data.json
  - subdir
    - local-data.py
    - hello.j2
    - subdir2
      - goodbye.j2
  index.md
```

The data from `global-data.json` will be available in all pages, but the data from `local-data.py` will only be available in `hello.j2` and `goodbye.j2`. 



Armed with the knowledge of data, you can now move on to [layouts](/tutorial/layouts/)