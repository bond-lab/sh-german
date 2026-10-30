# sh-german: the Sherlock Holmes canon in German

German translations of Arthur Conan Doyle's Sherlock Holmes stories and
novels, taken from [Projekt Gutenberg-DE](https://projekt-gutenberg.org),
as plain text and as [NTU Multilingual Corpus](https://github.com/bond-lab/NTUMC)
XML for sense annotation and alignment with the English canon in the
NTU-MC.  Documents are named by the canonical four-letter abbreviations
of Jay Finley Christ (1947), lowercased, as the English documents in the
NTU-MC are (`spec`, `danc`, `3stu`, ...).

The 45 documents are one version per story, from the translations
published by Robert Lutz, Stuttgart, 1902-1907 (Sherlock Holmes-Serie)
and the Franckh'sche Verlagshandlung and Dürr & Weber reissues of the
1920s-30s.  Doyle died in 1930 and these translations are over 90 years
old; they are in the public domain, with the caveats under *Copyright*
below.

What is not here: Projekt Gutenberg-DE has no old translation of *The
Hound of the Baskervilles* (Lutz, 1903) nor of the later stories, so 14
stories of the canon (`3gab`, `3gar`, `blan`, `card`, `cree`, `illu`,
`last`, `lion`, `maza`, `reti`, `shos`, `suss`, `thor`, `veil`) and the
*Hound* are missing.  The modern translations on Projekt Gutenberg-DE
(which cover `3gar` and the *Hound*), a 2023 compilation of old Franckh
translations and the separate 1902 Lutz printings of four stories are
under copyright or duplicates, and live in a sister repository,
`sh-german-other` (private), built with the same scripts and numbered
so that both load into one NTU-MC database.

## Layout

```
sources.toml       which Gutenberg-DE pages hold which story, edition and
                   translator, and where editorial text begins and ends;
                   the [corpus] table gives the corpus name, licence and
                   document-number offset
texts/             one file per document (see "Text format")
ntumc/             the same as NTU-MC XML, one file per document
ntumc/ntumc.dtd    the DTD (copied from the NTUMC repository)
scripts/fetch.py   download the pages listed in sources.toml into raw/
scripts/pg_extract.py   HTML page -> paragraphs
scripts/build_texts.py  raw/ -> texts/
scripts/ntumc_xml.py    texts/ -> NTU-MC XML (spaCy de_core_news_sm)
raw/               the downloaded HTML (not in git)
```

To rebuild everything:

```
uv run scripts/fetch.py
uv run scripts/build_texts.py
uv run scripts/ntumc_xml.py            # or a list of docs
```

To check and load the XML with the NTUMC tools:

```
NTUMC/scripts/corpus_xml.py validate ntumc/spec.xml
for f in ntumc/*.xml; do NTUMC/scripts/corpus_xml.py load $f --outdir build; done
```

## Text format

The first line is `# Title`; part and chapter headings are `## ` and
`### ` lines; paragraphs are separated by blank lines.  A paragraph
starting with `> ` is **editorial**: not Doyle's text but something the
German edition added, kept so that the documents match their source but
marked so that it is not aligned with the English:

- the frame narrative of the Franckh reissues of *Der Bund der
  Rothaarigen* (1936: Watson tells the stories to guests) and *Das
  getupfte Band* (1939: Holmes reads Watson's articles by the fire),
  which opens each volume and links the stories;
- the preface *Ein für allemal* in *Der sterbende Sherlock Holmes*;
- closing lines such as "Schluß des fünften Bandes" and "Ende".

The pictures of the dancing-men cipher are dropped and the sentences
around them rejoined; the decoded cipher lines stay.

## NTU-MC XML

Each file is one `<Corpus>` with one `<Document>` (language `deu`,
collection `story`, genre `fiction`) in the format of `ntumc.dtd`
(documented in the NTUMC repository under `docs/corpus-xml.md`).  The
document opens with the title (`h1`), the author (`author`), the English
title in parentheses and a translator line (`translator`), as the Italian
*La banda maculata* in the NTU-MC does; then the paragraphs, with `pid`
and stype `p` on each paragraph's first sentence.  Editorial sentences
carry `comment="editorial: ..."`.

Document numbers are 1-45 (the manifest order; `sh-german-other` starts
at 101) and sentence numbers are `10000 * N + i`, so all the files load
into one database without renumbering.  Tokens, lemmas, STTS tags (`pos`) and universal tags
(`upos`) come from spaCy `de_core_news_sm` 3.8.0.  spaCy's sentence
splits are post-processed to match the English side: a sentence is
joined to the one before when that one does not end in sentence-final
punctuation (spaCy breaks before a capitalised `Sie`, inside names such
as `Sherlock | Holmes` and after abbreviations such as `Mrs.`), when
either is punctuation alone or an initial, or when it starts with a
lowercase word (clauses after `;`, `:` and `,`); opening quotes are
moved to the sentence they open.  Punctuation keeps its surface form
as lemma.  There are no sense tags yet; sentence alignments to the
English canon are described below.

## Copyright

Doyle's originals are public domain everywhere.  For the translations the
German term is 70 years after the translator's death:

- Margarete Jacobi (1840-1910): clear.
- Louis Ottmann (publications 1886-1911) and Rudolf Lautenbach
  (publications 1894-1921): no life dates found, but almost certainly
  dead for more than 70 years.
- Adolf Gleiner, Johannes Hartmann, H. O. Herzog, and the unnamed
  translators of *Späte Rache* and *Das Zeichen der Vier* and the
  unnamed editor who wrote the Franckh frame narrative: no information;
  the Franckh and Dürr & Weber volumes (1920s-30s) are the least certain.
- The modern translations are copyright their translators and are not
  in this repository.

The scripts and metadata are under the MIT licence (see LICENSE).

## Documents

| doc | German title | English title | Source volume | Publisher, year | Translator |
|---|---|---|---|---|---|
| stud | Späte Rache | A Study in Scarlet | Späte Rache | Verlag von Robert Lutz, Stuttgart, 1902 | not named |
| sign | Das Zeichen der Vier | The Sign of Four | Das Zeichen der Vier | Verlag von Robert Lutz, Stuttgart, 1902 | not named |
| scan | Skandalgeschichte im Fürstentum O... | A Scandal in Bohemia | Der Bund der Rothaarigen und andere Detektivgeschichten | Verlag von Robert Lutz, Stuttgart, 1902 | Louis Ottmann und Margarete Jacobi |
| redh | Der Bund der Rothaarigen | The Red-Headed League | Der Bund der Rothaarigen und andere Detektivgeschichten | Verlag von Robert Lutz, Stuttgart, 1902 | Louis Ottmann und Margarete Jacobi |
| bosc | Der Mord im Tale von Bascombe | The Boscombe Valley Mystery | Der Bund der Rothaarigen und andere Detektivgeschichten | Verlag von Robert Lutz, Stuttgart, 1902 | Louis Ottmann und Margarete Jacobi |
| stoc | Eine sonderbare Anstellung | The Adventure of the Stockbroker's Clerk | Der Bund der Rothaarigen und andere Detektivgeschichten | Verlag von Robert Lutz, Stuttgart, 1902 | Louis Ottmann und Margarete Jacobi |
| twis | Der Mann mit der Schramme | The Man with the Twisted Lip | Der Bund der Rothaarigen und andere Detektivgeschichten | Verlag von Robert Lutz, Stuttgart, 1902 | Louis Ottmann und Margarete Jacobi |
| blue | Die Geschichte des blauen Karfunkels | The Adventure of the Blue Carbuncle | Der Bund der Rothaarigen und andere Detektivgeschichten | Verlag von Robert Lutz, Stuttgart, 1902 | Louis Ottmann und Margarete Jacobi |
| spec | Das getupfte Band | The Adventure of the Speckled Band | Das getupfte Band und andere Detektivgeschichten | Verlag von Robert Lutz, Stuttgart, 1902 | Louis Ottmann und Margarete Jacobi |
| engr | Der Daumen des Ingenieurs | The Adventure of the Engineer's Thumb | Das getupfte Band und andere Detektivgeschichten | Verlag von Robert Lutz, Stuttgart, 1902 | Louis Ottmann und Margarete Jacobi |
| nobl | Die verschwundene Braut | The Adventure of the Noble Bachelor | Das getupfte Band und andere Detektivgeschichten | Verlag von Robert Lutz, Stuttgart, 1902 | Louis Ottmann und Margarete Jacobi |
| bery | Die Geschichte des Beryll-Kopfschmuckes | The Adventure of the Beryl Coronet | Das getupfte Band und andere Detektivgeschichten | Verlag von Robert Lutz, Stuttgart, 1902 | Louis Ottmann und Margarete Jacobi |
| silv | Silberstrahl | The Adventure of Silver Blaze | Das getupfte Band und andere Detektivgeschichten | Verlag von Robert Lutz, Stuttgart, 1902 | Louis Ottmann und Margarete Jacobi |
| copp | Das Landhaus in Hampshire | The Adventure of the Copper Beeches | Das getupfte Band und andere Detektivgeschichten | Verlag von Robert Lutz, Stuttgart, 1902 | Louis Ottmann und Margarete Jacobi |
| five | Fünf Apfelsinenkerne | The Five Orange Pips | Fünf Apfelsinenkerne und andere Detektivgeschichten | Verlag von Robert Lutz, Stuttgart, 1902 | Louis Ottmann und Margarete Jacobi |
| musg | Der Katechismus der Familie Musgrave | The Adventure of the Musgrave Ritual | Fünf Apfelsinenkerne und andere Detektivgeschichten | Verlag von Robert Lutz, Stuttgart, 1902 | Louis Ottmann und Margarete Jacobi |
| reig | Die Gutsherren von Reigate | The Adventure of the Reigate Squire | Fünf Apfelsinenkerne und andere Detektivgeschichten | Verlag von Robert Lutz, Stuttgart, 1902 | Louis Ottmann und Margarete Jacobi |
| croo | Der Krüppel | The Adventure of the Crooked Man | Fünf Apfelsinenkerne und andere Detektivgeschichten | Verlag von Robert Lutz, Stuttgart, 1902 | Louis Ottmann und Margarete Jacobi |
| resi | Der Doktor und sein Patient | The Adventure of the Resident Patient | Fünf Apfelsinenkerne und andere Detektivgeschichten | Verlag von Robert Lutz, Stuttgart, 1902 | Louis Ottmann und Margarete Jacobi |
| nava | Der Marinevertrag | The Adventure of the Naval Treaty | Fünf Apfelsinenkerne und andere Detektivgeschichten | Verlag von Robert Lutz, Stuttgart, 1902 | Louis Ottmann und Margarete Jacobi |
| fina | Das letzte Problem | The Adventure of the Final Problem | Fünf Apfelsinenkerne und andere Detektivgeschichten | Verlag von Robert Lutz, Stuttgart, 1902 | Louis Ottmann und Margarete Jacobi |
| empt | Im leeren Hause | The Adventure of the Empty House | Als Sherlock Holmes aus Lhassa kam | Verlag von Robert Lutz, Stuttgart, 1905 | Rudolf Lautenbach und Adolf Gleiner |
| norw | Der Baumeister von Norwood | The Adventure of the Norwood Builder | Als Sherlock Holmes aus Lhassa kam | Verlag von Robert Lutz, Stuttgart, 1905 | Rudolf Lautenbach und Adolf Gleiner |
| yell | Das gelbe Gesicht | The Adventure of the Yellow Face | Als Sherlock Holmes aus Lhassa kam | Verlag von Robert Lutz, Stuttgart, 1905 | Rudolf Lautenbach und Adolf Gleiner |
| gree | Der griechische Dolmetscher | The Adventure of the Greek Interpreter | Als Sherlock Holmes aus Lhassa kam | Verlag von Robert Lutz, Stuttgart, 1905 | Rudolf Lautenbach und Adolf Gleiner |
| glor | Holmes' erstes Abenteuer | The Adventure of the Gloria Scott | Als Sherlock Holmes aus Lhassa kam | Verlag von Robert Lutz, Stuttgart, 1905 | Rudolf Lautenbach und Adolf Gleiner |
| gold | Der goldene Klemmer | The Adventure of the Golden Pince-Nez | Als Sherlock Holmes aus Lhassa kam | Verlag von Robert Lutz, Stuttgart, 1905 | Rudolf Lautenbach und Adolf Gleiner |
| soli | Die einsame Radfahrerin | The Adventure of the Solitary Cyclist | Als Sherlock Holmes aus Lhassa kam | Verlag von Robert Lutz, Stuttgart, 1905 | Rudolf Lautenbach und Adolf Gleiner |
| danc | Die tanzenden Männchen | The Adventure of the Dancing Men | Die tanzenden Männchen und andere Detektivgeschichten | Verlag von Robert Lutz, Stuttgart, 1906 | Rudolf Lautenbach |
| prio | Die Entführung aus der Klosterschule | The Adventure of the Priory School | Die tanzenden Männchen und andere Detektivgeschichten | Verlag von Robert Lutz, Stuttgart, 1906 | Rudolf Lautenbach |
| blac | Der schwarze Peter | The Adventure of Black Peter | Die tanzenden Männchen und andere Detektivgeschichten | Verlag von Robert Lutz, Stuttgart, 1906 | Rudolf Lautenbach |
| sixn | Die sechs Napoleonbüsten | The Adventure of the Six Napoleons | Die tanzenden Männchen und andere Detektivgeschichten | Verlag von Robert Lutz, Stuttgart, 1906 | Rudolf Lautenbach |
| abbe | Der Mord in Abbey Grange | The Adventure of the Abbey Grange | Die tanzenden Männchen und andere Detektivgeschichten | Verlag von Robert Lutz, Stuttgart, 1906 | Rudolf Lautenbach |
| seco | Der zweite Blutflecken | The Adventure of the Second Stain | Die tanzenden Männchen und andere Detektivgeschichten | Verlag von Robert Lutz, Stuttgart, 1906 | Rudolf Lautenbach |
| chas | Sherlock Holmes als Einbrecher | The Adventure of Charles Augustus Milverton | Sherlock Holmes als Einbrecher: Neue Sherlock Holmes-Geschichten | Verlag von Robert Lutz, Stuttgart, 1907 | Rudolf Lautenbach |
| 3stu | Die drei Studenten | The Adventure of the Three Students | Sherlock Holmes als Einbrecher: Neue Sherlock Holmes-Geschichten | Verlag von Robert Lutz, Stuttgart, 1907 | Rudolf Lautenbach |
| miss | Der vermißte Fußballspieler | The Adventure of the Missing Three-Quarter | Sherlock Holmes als Einbrecher: Neue Sherlock Holmes-Geschichten | Verlag von Robert Lutz, Stuttgart, 1907 | Rudolf Lautenbach |
| dyin | Der sterbende Sherlock Holmes | The Adventure of the Dying Detective | Der sterbende Sherlock Holmes und andere Detektivgeschichten | Franckh'sche Verlagshandlung, Stuttgart, n.d. | Johannes Hartmann |
| wist | Das Geheimnis der Villa Wisteria | The Adventure of Wisteria Lodge | Der sterbende Sherlock Holmes und andere Detektivgeschichten | Franckh'sche Verlagshandlung, Stuttgart, n.d. | Johannes Hartmann |
| redc | Der rote Kreis | The Adventure of the Red Circle | Der sterbende Sherlock Holmes und andere Detektivgeschichten | Franckh'sche Verlagshandlung, Stuttgart, n.d. | Johannes Hartmann |
| lady | Das Verschwinden der Lady Frances Carfax | The Disappearance of Lady Frances Carfax | Der sterbende Sherlock Holmes und andere Detektivgeschichten | Franckh'sche Verlagshandlung, Stuttgart, n.d. | Johannes Hartmann |
| bruc | Die gestohlenen Zeichnungen | The Adventure of the Bruce-Partington Plans | Der sterbende Sherlock Holmes und andere Detektivgeschichten | Franckh'sche Verlagshandlung, Stuttgart, n.d. | Johannes Hartmann |
| devi | Das Abenteuer mit dem Teufelsfuß | The Adventure of the Devil's Foot | Der sterbende Sherlock Holmes und andere Detektivgeschichten | Franckh'sche Verlagshandlung, Stuttgart, n.d. | Johannes Hartmann |
| iden | Ein Fall geschickter Täuschung | A Case of Identity | Der sterbende Sherlock Holmes und andere Detektivgeschichten | Franckh'sche Verlagshandlung, Stuttgart, n.d. | Johannes Hartmann |
| vall | Das Tal des Grauens | The Valley of Fear | Das Tal des Grauens | Dürr & Weber, Leipzig, n.d. | H. O. Herzog |

## Sentence alignment with the English canon

`alignment/eng-deu.tsv` links the German sentences to the English
sentences of the same stories in the NTU-MC (`eng.db`, documents
440-499; `eng_sid` is the English sentence id there, `deu_sid` the
German id of `ntumc/*.xml`).  One row per sentence pair; a German
sentence linked to two English sentences has two rows, and sentences
the translator dropped or added have none.  Editorial sentences and the
front matter were not aligned.

The links were made with [Bertalign](https://github.com/bfsujason/bertalign)
(LaBSE embeddings, two-pass dynamic programming) by
`scripts/align-sentences.py` of the [IMI](https://github.com/bond-lab/IMI)
repository (`usrname` bertalign, `conf` = cosine similarity of the two
sides), and every bead that was not a confident 1-1 link, about 13 %,
was checked by hand and re-cut where wrong (`usrname` claude,
`ltype` auto): about 3 % of all beads changed, mostly English sentences
the translator had dropped and the aligner had folded into a
neighbouring bead, and short dialogue turns attached to the wrong
neighbour.  `fix-sentence-links.py` in IMI applies such corrections,
`review-sentence-links.py` lists the doubtful beads.
