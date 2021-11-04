## Intro

This is the static blog generator I use for [agateau.com](https://agateau.com). It's a fork of Arnin Ronacher's [rstblog][] project.

[rstblog]: https://github.com/mitsuhiko/rstblog

This generator is tweaked for my needs, you are welcome to play with it, but you are pretty much on your own.

## Pages front matter

Pages must start with a YAML front matter.

There must be a blank line between the front matter and the content.

Front matter can be surrounded by `---` lines, but this is not necessary.

### Front matter entries

Required entries:

- `pub_date`: date: following the format "YYYY-MM-DD hh:mm:ss +hh:mm".
- `public`: boolean: must be `true` for the article to be visible.
- `title`: string: the page title.
- `tags`: array of string: the page tags. Can be left empty.

Optional entries:

- `comments`: boolean: set to `false` to disable comments.
- `jinja`: boolean: set to `true` to use Jinja template commands in the article.

## Pages summary

Use `<!-- break -->` inside an article to define its summary.

## Pages data

For a given `$page.md` file, if a `$file.yml` exists, its content is included in the context available to Jinja commands for the page.

## Custom rst directives

### gallery

Creates a gallery of images.

Syntax:

```
.. gallery ::
    :thumbsize: <int>  # thumbnail size in pixels, default to 200
    :square:           # set this to generate square thumbnails
    :images: <path>    # path to a yaml file relative to the document listing the images to show
                       # see below
    <content>          # images to show, see below
```

Images to show are defined as a YAML array. The array can either be define as the content of the directive, or in a YAML file, using the `:images:` argument.

The items in the YAML array are a YAML object with two keys:

- `full`: The path to the full-size image, relative to the document.
- `alt`: The image caption.


### thumbimg

An image directive with automatic thumbnail generation.

Syntax:

```
.. thumbimg :: <image-path>  # path to the full-size image
    :thumbsize: <int>        # thumbnail size in pixels, default to 300
```
