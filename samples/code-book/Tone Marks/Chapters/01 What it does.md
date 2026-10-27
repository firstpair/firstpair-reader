# What it does

`tone_marks.py` reads pinyin with tone numbers, as typed on a keyboard without accents, and writes it with tone marks: `ni3 hao3` becomes `nǐ hǎo`, and `xue2 er2 shi2 xi2 zhi1` becomes `xué ér shí xí zhī`.

The whole program is one substitution over the line:

```firstpair-fragment
{"id": "convert"}
```

and a loop over standard input:

```firstpair-fragment
{"id": "main"}
```

Try it: `echo 'Dao4 ke3 dao4' | python3 tone_marks.py`.
