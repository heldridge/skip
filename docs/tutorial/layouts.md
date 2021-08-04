---

---

# Layouts

Any source file can be rendered as content inside of another template.

Make a new subfolder in the `skip-example` directory called `templates`:

``` bash
>>> mkdir templates
```

Next, create a template inside that folder

``` jinja2
<!-- templates/my-template.j2 -->

<header> Here is my header! </header>

{{ content }}

<footer> Here is my footer! </footer>

```

Now, change `index.md` from the Getting Started tutorial to the following:

``` markdown
---
layout: my-template
---

# Hello World!
```

Your `index.html` in the site folder will now be rendered with the header and footer from the layout.