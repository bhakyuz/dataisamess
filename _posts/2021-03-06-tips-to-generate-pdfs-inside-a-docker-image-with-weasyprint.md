---
layout: post
title: "Tips while creating PDFs inside a docker image with WeasyPrint"
author: "bhakyuz"
tags: ["weasyprint", "pdf", "html", "pandas", "docker"]
---

Recently at [Homagames](homagames.com), we wanted to improve certain pdf reports that we are producing once a month. PDF reports were already in place but they were generated via an excel sheet and it was not quite simple to make some modifications. And we only wanted to create single-page pdf documents following the same structure we had. In this article, you'll learn about the main takeaways while creating pdf with [WeasyPrint](https://weasyprint.org/).

## Create an HTML template and a style sheet(css file)

That is the most obvious one. To have a decent pdf, we need a template in HTML format and a stylesheet that defines how the HTML template is presented.

- Keep the HTML simple

  In the HTML file, we have hardcoded some parts that do not seem very likely to change often. For other parts, we leverage jinja2 to make documents more dynamic. For example, the following is how we sequentially print many small tables:

```html
{% for item in tables %} {{ item }}
<br />
{% endfor %}
```

- Minimal css

  For the CSS, we have introduced only what we needed. The main headache was here was having slightly different table formatting across the document. To overcome this, we have used different classes for different needs. Something similar to the following:

```css
.table-info {
  border: 2px solid black;
}
.table-data {
  border: 1px solid black;
}
```

## One report >> One directory

When you finally arrive at the point that you are to render your reports, you will realize that `WeasyPrint` needs a bit of context. If the logo or CSS sheet that you are using is not in a good place, your report won't be rendered as you expected.
For that, we keep everything in one directory called `assets` then one directory for each report (we only have one for the time being ).

```sh
├── assets
│   └── some_report
│       ├── logo.png
│       ├── style.css
│       └── template.html
```

When we render documents via `WeasyPrint`, we provide the path for the report directory. If we do not pass base_url as in the following snippet, WeasyPrint won't be able to place desired styles (`style.css`) neither the logo (`logo.png`) in the generated pdf file.

```py
template_dir = 'assets/some_report/'

with open(os.path.join(template_dir, 'template.html')) as f:
    jinja_template = Template(f.read())

rendered = jinja_template.render({'tables': tables})
pdf = weasyprint.HTML(string=rendered, base_url=template_dir).write_pdf()
```

## Convert tables to HTML with Pandas

Generating table-like data in HTML is not trivial. If we wanted to create HTML files from scratch, that would take quite some time for us. Instead, we use `pandas` [to_html](https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.to_html.html) method.

We are passing class input here as we have defined in our CSS file.

```py
a_dataframe.to_html(
    classes=["table-info"], index=False, border=0, justify='unset'),

another_dataframe.to_html(
    classes=["table-data"], index=False, border=0, header=False),

```

Then the main difficulty that we are left with is preparing the tables in a good format, with the right labels, only a few columns, etc. This is the usual problem e.g. 80/20: 80% data cleaning, 20% actual data analysis. It takes some thinking to put data good structure for the final pdf. For that:

- We created simple methods to convert a wider data frame to a longer format with desired columns. These methods were simple enough to follow and reuse for multiple tables.
- For number formatting, (mainly for multiple currencies), we again introduced some helper functions to convert numeric data to `str`, so that we don't have to add these formatting rules in the CSS stylesheet. (For multiple currencies, it might be a nightmare to handle everything in CSS)

## Be careful with fonts (especially inside docker images)

The biggest issue I had was just after I deployed my code in preproduction. Everything had been working well in my local machine, I had arranged the structure and font size so that it was fitting nicely on a single page. Once I generated pdf in preproduction, pdf reports did not seem the same.

I had font specified in my stylesheet like this:

```css
body {
  font-family: "Helvetica";
}
```

I was naively assuming that I was producing pdf reports with `Helvetica` font. But in my local Ubuntu machine, I did not even have that font. It fallback to another font.

So the solution is simple enough; just make sure that the font you want to use exists in your machine/docker image. `fc-list` can be useful to see what fonts you have installed.

```sh
fc-list
/usr/share/fonts/truetype/lato/Lato-Medium.ttf: Lato,Lato Medium:style=Medium,Regular
/usr/share/fonts/truetype/tlwg/TlwgTypo-Bold.ttf: Tlwg Typo:style=Bold
/usr/share/fonts/truetype/lato/Lato-SemiboldItalic.ttf: Lato,Lato Semibold:style=Semibold Italic,Italic
/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf: DejaVu Serif:style=Bold
/usr/share/fonts/opentype/urw-base35/URWBookman-LightItalic.otf: URW Bookman:style=Light Italic
...
```

If you run this code in a bare docker image, you will realize that you don't have many. I had only 3 of them:

- DejaVu Serif
- DejaVu Sans
- DejaVu Sans Mono

To overcome my problem, I adapted my CSS with `DejaVu Serif`. This required modifying font size here and there to fit the report on a single page. In the end, I was able to produce exactly the same pdfs both in my local machine and preproduction/production.
If you are willing to use other fonts, make sure that they are installed in your docker image.

## Conclusion

I wanted to share a small experience while creating pdf documents with `WeasyPrint`. Hope that the tips that I have shared would save you some time if you are planning to generate some pdf reports with `WeasyPrint`.
