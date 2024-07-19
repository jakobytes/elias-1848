# Source data format

The source files for the FILTER pipeline are generally XML files
containing text, some metadata and footnotes, while further data can be
supplied in additional files (typically tables in CSV format).

## General description of the XML format

The basic structure of the XML files is as follows:
```xml
<KOKONAISUUS>
  <ITEM nro="..." p="..." y="..." k="...">
  <META>
    ...
  </META>
  <TEXT>
    ...
  </TEXT>
  <REFS>
    ...
  </REFS>
  </ITEM>
  ...
</KOKONAISUUS>
```

The name of the top-level node is not important for the FILTER
pipeline. It is called `<KOKONAISUUS>` in SKVR, but might be different
in other collections. This node contains a list of `<ITEM>` nodes,
each of them corresponding to one poem.

The `<ITEM>` nodes consist of three parts: `<META>`, `<TEXT>` and
`<REFS>`, with the last one being optional. The node also has four attributes: 
`nro` (poem ID), `p` (place ID), `k` (collector ID), `y` (year).
The attributes `p`, `k`, `y` are optional and sometimes referred to as
**structured metadata**. The place and collector IDs should contain a
prefix denoting the collection in which they are defined, e.g. `skvr_`
or `erab_`. It is allowed to use IDs coming from another collection,
e.g. Elias Lönnrot (`skvr_77`) can be referred to with the same ID also
in JR and KR. Multiple collector and place IDs are allowed, separated
with semicolon (`;`) **without spaces**.

### `<META>`

The section `<META>` contains what is often called
**unstructured metadata** or **raw metadata**. Here is an example coming
from SKVR:
```xml
<META>
  <OSA>I1</OSA>
  <ID>1. </ID>
  <LOC>Kellovaara. </LOC>
  <COL>Lönnrot </COL>
  <SGN>A II 9, n. 12. </SGN>
  <TMP>- 24/4 1835.</TMP>
  <INF>
  Miihkalin&#769;e Simana. - Mp. metsäpirtissä Tsirkkakemin ja Jyskyjärven 
  välillä.
  </INF>
</META>
```

The section consists of a list of elements containing no attributes and
free-form text values. The names of the tags are not generally
standardized, but consistent at least within a collection.

In some collections, some tags may contain another level of internal
structure, e.g. (in ERAB):
```xml
<INF><NIMI>Marie Kivi</NIMI>, <ELUL>65 a</ELUL></INF>
```

The preprocessing pipeline converts this kind of metadata to a
three-column table `poem_id,field,value`, with structure being flattened -
e.g. the above entries would be converted to field names `INF_NIMI` and
`INF_ELUL`.

The values of the metadata fields may also contain references to
footnotes, but these are much more common in the text, and thus described
in the next section.

### `<TEXT>`

The section `<TEXT>` contains poem text. It is generally a sequence of
*verses*, each verse being an element containing text. The name of
the tag corresponds to the type of the verse, with the following types
being commonly used:
* `<CPT>` - a heading (often poem title)
* `<K>` - remarks by the editor or publisher, not included in the original manuscript (TODO check)
* `<L>` - prose part of the collected text
* `<V>` - a poetic line

In addition, the verse text may include XML elements related to formatting, like:
* `<KA>` - a bow linking co-articulated consonants of diphthongs,
* `<I>` - cursive,
* `<SUP>` - superscript,
* etc.

See [issue #34](https://github.com/hsci-r/filter-data-pipeline/issues/34)
for a complete list with examples and information on how verse-internal
markup is currently dealt with.

The verse text may also contain references to footnotes, either in a
structured form, like `<REFNR>1</REFNR>` (ERAB), or unstructured form,
like `#1` (SKVR, JR).

### `<REFS>`

This section contains footnotes, either as unstructured text (SKVR, JR)
or in a more structured form (ERAB). See the next section for details.

## Collection-specific details

### SKVR

#### `<ITEM>` tag attributes

The attributes `p` and `k` always contain a single ID.

For the attribute `y`, the value `9999` denotes unknown year.

#### Text

The text verses might commonly include verse numbers of every fifth
verse as part of the text.

> [!NOTE]
> It would be desirable to mark the verse numbers with a separate element,
> so that they can more easily be removed or treated specially.

#### Footnotes

The footnotes in SKVR are provided in free text form. Typically a new
footnote starts by `#`+footnote number at the beginning of the line
(typically after some spaces). Extra line breaks and whitespace,
or occasionally missing line breaks, make parsing error-prone,
e.g. (`skvr04124080`):
```xml
                <REFS>
  #1 Vrt. Pieni Runoseppä, s. 19.
  #2 = käyrästä puusta tehty.
  #3 jos ois' pora = jo olisi aika; ven. #3 jos#4 = jouto-aika; johtuu sabatti
    sanasta.
</REFS>
```

> [!NOTE]
> It would be desirable to convert the footnotes to a more structured,
> ERAB-like format. Right now it is attempted automatically
> by the functions [insert_refnrs()](https://github.com/hsci-r/filter-data-pipeline/blob/master/code/common_xml_functions.py#L28-L39)
> and [parse_skvr_refs()](https://github.com/hsci-r/filter-data-pipeline/blob/master/code/common_xml_functions.py#L42-L70),
> but this is prone to errors.

### ERAB

#### `<ITEM>` tag attributes

The attributes `p` and `k` are not used as the place and collector
information is provided in separate tables: `laul_koht.csv` and
`laul_koguja.csv`.

For the attribute `y`, the value `0` or empty denotes unknown year.

#### Metadata

TODO

#### Text

The poem texts might include additional tags of type `<PAG>` (containing
page numbers, removed in the pipeline) and `<TYHI>` (empty lines).

The verse texts might contain the tag `<REFR>` marking inline refrains,
while the `<TEXT>` element might contain the tag `<RREFR>` marking
refrains consisting of entire lines (and itself containing `<V>`
elements). Examples:
```xml
<V>Sisse isti Simmukene <REFR>Jaanika</REFR></V>
```

```xml
<RREFR><V>Virvaivi, virvaije</V>
<V>Virvai kompari</V></RREFR>
```

#### Footnote format

The footnote format in ERAB is more structured than in the Finnish
collections. References to footnotes are marked using a tag `<REFNR>`
or `<MRKSNR>`, with the footnote number as text content inside.

The section `<REFS>` contains a list of elements of type either `<REF>`
or `<MRKS>`.

> [!WARNING]
> It is not clear to me (Maciej) what the difference between `<MRKS>`
> and `<REF>` is. Currently only `<REFNR>` is processed into references
> in the text.

### JR

#### `<ITEM>` tag attributes

The attributes `p` and `k` often contain multiple IDs separated with
semicolons.

#### Metadata

The `<LOC>` elements in the raw metadata typically have an internal structure,
consisting of the following elements:
* `<AREA>` - single-letter area code,
* `<PAR>` - parish,
* `<VIL>` - village.

Also the `<INF>` tags have an internal structure, containing:
* `<NAME>` - the name of the informant,
* `<CTX>` - free-form text, usually also including the name of the informant, but with possible additional information (age, place of birth, from where do they know the song etc.).

### KR

TODO

## Supplementary files

TODO

### SKVR

TODO

### ERAB

TODO

### JR

TODO