---
title: Collections
date: "2021-01-05"
---

# Collections

Skip lets you use lists of pages in your templates.
These lists are referred to as **collections**.

Create a new subdirectory in your project called `dogs`:

``` bash
>>> mkdir dogs
```

Now fill it with three files describing some breeds:

``` markdown
<!-- dogs/mastiff.md -->

---

tags:
    - dogs
    - large
name: Mastiff

---

# Mastiff

A large and powerful dog
```

``` markdown
<!-- dogs/border-collie.md -->

---

tags: 
    - dogs
    - medium
name: Border Collie

---

# Border Collie

A working and hearding dog
```

``` markdown
<!-- dogs/labrador.md -->

---

tags: 
    - dogs
    - medium
name: Labrador

---

# Labrador

A popular retriever dog
```

Great! After generating the site again you should now have these three pages in a `/dog/` folder.

Skip takes each file that has a `tags` attribute and adds it to a collection for each of its tags.
So if we want to loop over our dog pages, we would use the `dogs` collection.
If we wanted to only loop over the medium-sized dogs, we would use the `medium` collection.

Lets add a link to each of our dog pages to a page called `dog-links.j2`

``` jinja2
<!-- dog-links.j2 -->

<ul>
    {% for dog_page in collections.dogs %}
    <li>
        <a href="{{ dog_page.get_permalink() }}">
            {{ dog_page.data.name }}
        </a>
    </li>
</ul>
```

Each page in the collection has a function `get_permalink()` that generates its url, as well as a `data` attribute that lets you use any of the data associated with the page. For more about what you can get from a page in a collection, see the [docs](/)