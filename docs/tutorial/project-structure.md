---
title: Project Structure
date: "2021-01-02"
---
# Project Structure

Skip builds your site according to your folder hierarchy.

Other than the special `index.html` file in the top level folder, the pages for
content files get created at the `/<subdir>/<filename>/index.html` path in the `_site`
directory.

Still in the `skip-example` directory, make a new content file:

``` bash
>>> echo "# Hello New Page" > new-page.md
```

Now, check out the `_site` directory (or go to [`localhost:8080/new-page/`](localhost:8080/new-page/) in your browser)
to see the generated html

## Subfolders

Create a subdirectory and two new content files inside of it:

``` bash
>>> mkdir subdir
>>> echo "# Subdir 1" > subdir/1.md
>>> echo "# Subdir 2" > subdir/2.md
```

You should now have site pages at the `/subdir/1/` and `/subdir/2/` paths.

## 

You're now ready to learn about [data](/tutorial/data/)