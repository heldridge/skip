---
title: Getting Started
date: "2021-01-01"
---
# Getting Started

First, make a project directory and cd into it.
All lines in code blocks that start with `>>>` are meant to be run as-is in the terminal.

``` bash
>>> mkdir skip-example
>>> cd skip-example
```

Next, you can install Skip from [PyPI](https://pypi.org/).

``` bash
>>> pip install skip-ssg
```

Add some content...

``` bash
>>> echo "# Hello World" > index.md
```

And run `skip`!

``` bash
>>> skip --serve
```

You should now be able to view your generated pages at [`localhost:8080`](localhost:8080)!

## 
You can now continue on to [project structure](/tutorial/project-structure/)