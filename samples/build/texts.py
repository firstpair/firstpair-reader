"""Source texts, translations, and word glosses for the sample vaults.

Source texts are in the public domain (see samples/README.md).  Every
English and Russian translation and every word gloss here was written for
these samples, except the edition marked as James Legge's (1891).

Chinese units come in two shapes:

* ``"zh"`` plain text, split into words by jieba (segment.py);
* ``"seg"`` text already split by hand, words separated by spaces.  A word
  may carry its reading as ``word=reading`` where the default pinyin would
  be wrong for this context (说=yuè in 不亦说乎).

Glosses are written ``"a / b / c"``, one per word in order, punctuation
skipped.  build.py fails when the counts disagree with segmented.json.
"""

# --------------------------------------------------------------------------
# 狂人日记 (Lu Xun, 1918): the preface and the first entry.  jieba splits it.
# --------------------------------------------------------------------------

LUXUN = {
    "folder": "Diary of a Madman",
    "title": "A Madman's Diary",
    "author": "Lu Xun (鲁迅)",
    "subtitle": "狂人日记 · 1918 · the preface and the first entry",
    "parts": [
        {"id": "P01", "title": "Preface", "note": "01 Preface"},
        {"id": "P02", "title": "The Diary", "note": "02 The Diary"},
    ],
    "pages": [
        {
            "id": "p001", "title": "Preface", "part": "P01",
            "units": [
                {
                    "kind": "cover",
                    "zh": "狂人日记",
                    "en": "A Madman's Diary",
                    "gloss_en": "madman / diary",
                },
                {
                    "zh": "某君昆仲，今隐其名，皆余昔日在中学校时良友；分隔多年，消息渐阙。"
                          "日前偶闻其一大病；适归故乡，迂道往访，则仅晤一人，言病者其弟也。"
                          "劳君远道来视，然已早愈，赴某地候补矣。",
                    "en": "Two brothers, whose names I withhold here, were both good friends of mine "
                          "in my middle-school days. After many years apart, news of them had "
                          "gradually dried up. Not long ago I happened to hear that one of them was "
                          "gravely ill, and as I was going back to my home town I went out of my way "
                          "to call on them. I found only one of them, who told me that the sick one "
                          "had been his younger brother. \"It was good of you to come so far to see "
                          "us,\" he said, \"but he recovered long ago and has gone off somewhere to "
                          "wait for an official post.\"",
                    "gloss_en": "a certain gentleman / brothers / now / conceal / their / names / all / my / "
                                "former days / at / middle school / time / good friends / be parted / "
                                "many years / news / gradually / be lacking / days ago / by chance / hear / "
                                "one of them / fall gravely ill / happen to / return to / home town / "
                                "make a detour / go / visit / but then / only / meet / one / person / say / "
                                "the sick one / his / younger brother / (it is) / trouble / you / long way / "
                                "come / see / but / already / long since / recover / go to / "
                                "a certain place / await a post / (final)",
                },
                {
                    "zh": "因大笑，出示日记二册，谓可见当日病状，不妨献诸旧友。"
                          "持归阅一过，知所患盖“迫害狂”之类。语颇错杂无伦次，又多荒唐之言；"
                          "亦不著月日，惟墨色字体不一，知非一时所书。"
                          "间亦有略具联络者，今撮录一篇，以供医家研究。",
                    "en": "Then, laughing heartily, he brought out two volumes of a diary, saying that "
                          "they would show what his brother's illness had been like at the time and "
                          "that there was no harm in giving them to an old friend. I took them home "
                          "and read them through, and saw that the trouble had been some kind of "
                          "\"persecution mania\". The writing is muddled and incoherent, full of wild "
                          "talk; it gives no dates, but the ink and the handwriting vary, so it was "
                          "plainly not written all at one time. Some passages do hang together a "
                          "little, and I have copied out a selection here as material for medical "
                          "research.",
                    "gloss_en": "thereupon / laugh heartily / bring out / diary / two volumes / say / "
                                "one can see / at that time / symptoms / no harm in / present / to / "
                                "old friend / take / home / read / once / through / know / what / "
                                "suffer from / probably / persecution / mania / that kind / language / "
                                "rather / jumbled / without / coherence / also / much / absurd / (of) / "
                                "talk / also / not / write down / month / day / only / ink colour / "
                                "handwriting / not / uniform / know / not / at one time / (what) / write / "
                                "here and there / also / there are / somewhat have / connection / ones / "
                                "now / pick out / copy / one piece / in order to / offer for / doctors / "
                                "research",
                },
                {
                    "zh": "记中语误，一字不易；惟人名虽皆村人，不为世间所知，无关大体，然亦悉易去。"
                          "至于书名，则本人愈后所题，不复改也。七年四月二日识。",
                    "en": "The diary's mistakes of language I have left exactly as they were. Only "
                          "the names, although they all belong to village people unknown to the "
                          "world and matter nothing to the whole, I have changed every one. As for "
                          "the title, it was given by the author himself after his recovery, and I "
                          "have not altered it. Noted on the second day of the fourth month of the "
                          "seventh year [of the Republic, 1918].",
                    "gloss_en": "diary / in / language / mistakes / not a word changed / only / people / "
                                "names / although / all / village / people / not / by / the world / known / "
                                "immaterial to the whole / yet / still / all / change / away / as for / "
                                "title / then / the man himself / recover / after / (what) / inscribe / "
                                "not / again / alter / (final) / year seven / fourth month / second day / "
                                "noted",
                },
            ],
        },
        {
            "id": "p002", "title": "Entry I", "part": "P02",
            "units": [
                {"kind": "heading", "zh": "一", "en": "I", "gloss_en": "one"},
                {
                    "zh": "今天晚上，很好的月光。",
                    "en": "Tonight the moonlight is very fine.",
                    "gloss_en": "today / evening / very / good / (of) / moonlight",
                },
                {
                    "zh": "我不见他，已是三十多年；今天见了，精神分外爽快。"
                          "才知道以前的三十多年，全是发昏；然而须十分小心。"
                          "不然，那赵家的狗，何以看我两眼呢？",
                    "en": "I had not seen it for more than thirty years; seeing it today, I feel "
                          "unusually clear-headed. Only now do I know that those thirty-odd years "
                          "were spent in a daze. But I must be very careful. Otherwise, why would "
                          "the Zhaos' dog have looked at me twice?",
                    "gloss_en": "I / not see / it (the moon) / already / be / thirty-odd years / today / "
                                "see / (done) / spirits / unusually / refreshed / only then / know / "
                                "before / (of) / thirty-odd years / entirely / be / in a daze / however / "
                                "must / extremely / careful / otherwise / that / the Zhao family / 's / "
                                "dog / why / look at / me / two glances / (question)",
                },
                {
                    "zh": "我怕得有理。",
                    "en": "I have good reason to be afraid.",
                    "gloss_en": "I / fear / (so that) / with reason",
                },
            ],
        },
    ],
}

# jieba adjustments for the Lu Xun text: words to keep whole or to split, and
# readings that the default pinyin gets wrong in this context.
LUXUN_JIEBA_WORDS = ["中学校", "迂道"]
LUXUN_JIEBA_SPLITS = [("狂人", "日记")]
LUXUN_READINGS = {
    "颇": "pō",        # rather (not pǒ)
    "得": "de",        # 怕得有理: complement particle
    "识": "zhì",       # 七年四月二日识: "noted", as in a preface's signature
    "间": "jiàn",      # 间亦有: occasionally
    "为": "wéi",       # 不为世间所知: passive 为…所
    "晚上": "wǎnshang",
    "消息": "xiāoxi",
    "精神": "jīngshen",
    "赵家": "Zhàojiā",
}

# --------------------------------------------------------------------------
# 论语 · 学而 1.1–1.4.  Hand-split; glosses in Russian (primary) and English.
# --------------------------------------------------------------------------

ANALECTS = {
    "folder": "Analects",
    "title": "Лунь юй · Беседы и суждения",
    "author": "Конфуций и его ученики",
    "subtitle": "论语 · 学而 1.1–1.4",
    "parts": [
        {"id": "P01", "title": "Глава 1. Учиться (学而)", "note": "01 Учиться"},
    ],
    "pages": [
        {
            "id": "p001", "title": "1.1", "part": "P01",
            "units": [
                {
                    "kind": "heading",
                    "seg": "学而 第一",
                    "ru": "Глава первая: «Учиться»",
                    "en": "Book One: \"Learning\"",
                    "gloss_ru": "«Учиться и…» / первая",
                    "gloss_en": "\"Learning and…\" / first",
                },
                {
                    "seg": "子=zǐ 曰 ： “ 学 而 时 习 之 ， 不 亦 说=yuè 乎 ？ 有 朋 自 远方 来 ， 不 亦 乐=lè 乎 ？ "
                           "人 不 知 而 不 愠 ， 不 亦 君子 乎 ？ ”",
                    "ru": "Учитель сказал: «Учиться и в своё время повторять выученное — разве это "
                          "не радость? Когда друг приходит издалека — разве это не веселье? Когда "
                          "люди тебя не знают, а ты не держишь обиды, — разве это не благородный муж?»",
                    "en": "The Master said: \"To learn, and at the proper times to practise what one "
                          "has learned: is that not a pleasure? To have a friend come from far away: "
                          "is that not a joy? To go unrecognised by others and feel no resentment: "
                          "is that not the mark of a gentleman?\"",
                    "gloss_ru": "Учитель / сказал / учиться / и / в своё время / повторять / это / не / "
                                "разве / радость / (вопрос) / есть / друг / из / дальние края / приходить / "
                                "не / разве / веселье / (вопрос) / люди / не / знать / а / не / обижаться / "
                                "не / разве / благородный муж / (вопрос)",
                    "gloss_en": "the Master / said / learn / and / at due times / practise / it / not / "
                                "indeed / delight / (question) / have / friend / from / far places / come / "
                                "not / indeed / joy / (question) / others / not / know / and yet / not / "
                                "resent / not / indeed / gentleman / (question)",
                },
            ],
        },
        {
            "id": "p002", "title": "1.2", "part": "P01",
            "units": [
                {
                    "seg": "有子=Yǒuzǐ 曰 ： “ 其 为=wéi 人 也 孝弟=xiàotì ， 而 好=hào 犯上 者 ， 鲜=xiǎn 矣 ； "
                           "不 好=hào 犯上 ， 而 好=hào 作乱 者 ， 未 之 有 也 。 "
                           "君子 务 本 ， 本 立 而 道 生 。 "
                           "孝弟=xiàotì 也 者 ， 其 为=wéi 仁 之 本 与=yú ！ ”",
                    "ru": "Учитель Ю сказал: «Редко бывает, чтобы человек, почтительный к родителям "
                          "и старшим братьям, любил перечить вышестоящим; а чтобы тот, кто не любит "
                          "перечить вышестоящим, любил сеять смуту, — такого не бывало никогда. "
                          "Благородный муж заботится о корне: когда корень утвердился, рождается путь. "
                          "Почтительность к родителям и старшим братьям — не в ней ли корень человечности?»",
                    "en": "Master You said: \"Few indeed are those who are dutiful to their parents "
                          "and elder brothers and yet like to defy their superiors; and there has "
                          "never been one who did not like to defy his superiors and yet liked to "
                          "stir up disorder. The gentleman attends to the root; when the root is "
                          "established, the Way grows from it. Being dutiful to parents and elder "
                          "brothers: is that not the root of humaneness?\"",
                    "gloss_ru": "Учитель Ю / сказал / тот / быть / человеком / (пауза) / почтительный к старшим / "
                                "но / любить / перечить вышестоящим / тот, кто / редко / (итог) / не / "
                                "любить / перечить вышестоящим / но / любить / сеять смуту / тот, кто / "
                                "не / такого / бывать / (итог) / благородный муж / заботиться о / корень / "
                                "корень / утвердиться / и / путь / рождаться / почтительность к старшим / "
                                "(подчёркивание) / то, что / это / быть / человечность / (род. падеж) / "
                                "корень / (восклицание)",
                    "gloss_en": "Master You / said / one / be / person / (pause) / dutiful to elders / "
                                "yet / like / defy superiors / one who / few / (final) / not / like / "
                                "defy superiors / yet / like / make trouble / one who / never / such / "
                                "exist / (final) / gentleman / attend to / root / root / be established / "
                                "and / the Way / grow / dutiful to elders / (emphasis) / that which / it / "
                                "be / humaneness / 's / root / (exclamation)",
                },
            ],
        },
        {
            "id": "p003", "title": "1.3", "part": "P01",
            "units": [
                {
                    "seg": "子=zǐ 曰 ： “ 巧言 令色 ， 鲜=xiǎn 矣 仁 ！ ”",
                    "ru": "Учитель сказал: «Искусные речи и угодливое лицо — редко в них бывает человечность!»",
                    "en": "The Master said: \"Clever words and an ingratiating face: seldom is there "
                          "humaneness in them!\"",
                    "gloss_ru": "Учитель / сказал / искусные речи / угодливое лицо / редко / (итог) / человечность",
                    "gloss_en": "the Master / said / clever words / ingratiating face / seldom / (final) / humaneness",
                },
            ],
        },
        {
            "id": "p004", "title": "1.4", "part": "P01",
            "units": [
                {
                    "seg": "曾子=Zēngzǐ 曰 ： “ 吾 日 三 省=xǐng 吾 身 ： 为=wèi 人 谋 而 不 忠 乎 ？ "
                           "与=yǔ 朋友 交 而 不 信 乎 ？ 传=chuán 不 习 乎 ？ ”",
                    "ru": "Учитель Цзэн сказал: «Каждый день я трижды проверяю себя: был ли я предан, "
                          "замышляя дела для других? Был ли я верен слову в общении с друзьями? "
                          "Не передавал ли я другим того, в чём сам не упражнялся?»",
                    "en": "Master Zeng said: \"Each day I examine myself on three counts. In planning "
                          "for others, have I failed to be loyal? In dealing with friends, have I "
                          "failed to keep my word? Have I passed on what I have not practised myself?\"",
                    "gloss_ru": "Учитель Цзэн / сказал / я / каждый день / трижды / проверять / мой / себя / "
                                "для / других / замышлять / и / не / преданный / (вопрос) / с / друзья / "
                                "общаться / и / не / верный слову / (вопрос) / передавать / не / "
                                "упражняться / (вопрос)",
                    "gloss_en": "Master Zeng / said / I / daily / three times / examine / my / self / for / "
                                "others / plan / and / not / loyal / (question) / with / friends / deal / "
                                "and / not / trustworthy / (question) / pass on / not / practise / (question)",
                },
            ],
        },
    ],
}

# --------------------------------------------------------------------------
# 道德经 1–3 (the Wang Bi text).  Hand-split; English glosses.
# --------------------------------------------------------------------------

DAODEJING = [
    {
        "id": "p001", "title": "Chapter 1", "zh_title": "第一章",
        "units": [
            {"seg": "道 可 道 ， 非 常 道 ； 名 可 名 ， 非 常 名 。",
             "gloss_en": "way / can / be told / not / constant / way / name / can / be named / not / constant / name"},
            {"seg": "无 名 天地 之 始 ； 有 名 万物 之 母 。",
             "gloss_en": "without / name / heaven and earth / 's / beginning / with / name / the ten thousand things / 's / mother"},
            {"seg": "故 常 无 欲 ， 以 观 其 妙 ； 常 有 欲 ， 以 观 其 徼=jiào 。",
             "gloss_en": "so / always / without / desire / thereby / see / its / subtlety / always / with / "
                         "desire / thereby / see / its / boundary"},
            {"seg": "此 两 者 ， 同 出 而 异 名 ， 同 谓 之 玄 。 玄 之 又 玄 ， 众 妙 之 门 。",
             "gloss_en": "these / two / ones / together / come out / but / differ / name / together / call / "
                         "them / dark / dark / (and) / again / dark / all / subtleties / 's / gate"},
        ],
    },
    {
        "id": "p002", "title": "Chapter 2", "zh_title": "第二章",
        "units": [
            {"seg": "天下 皆 知 美 之 为=wéi 美 ， 斯 恶=è 已 ； 皆 知 善 之 为=wéi 善 ， 斯 不 善 已 。",
             "gloss_en": "all under heaven / all / know / beauty / (subj.) / as / beauty / then / ugliness / "
                         "already / all / know / good / (subj.) / as / good / then / not / good / already"},
            {"seg": "故 有 无 相=xiāng 生 ， 难 易=yì 相=xiāng 成 ， 长=cháng 短 相=xiāng 形 ， "
                    "高 下 相=xiāng 倾 ， 音 声 相=xiāng 和=hè ， 前 后 相=xiāng 随 。",
             "gloss_en": "so / being / non-being / each other / give birth / hard / easy / each other / complete / "
                         "long / short / each other / shape / high / low / each other / lean on / note / "
                         "voice / each other / answer / before / after / each other / follow"},
            {"seg": "是以 圣人 处=chǔ 无为 之 事 ， 行 不 言 之 教=jiào ；",
             "gloss_en": "therefore / the sage / abide in / not-doing / 's / work / practise / not / speak / 's / teaching"},
            {"seg": "万物 作 焉 而 不 辞 ， 生 而 不 有 ， 为=wéi 而 不 恃 ， 功 成 而 弗 居 。 "
                    "夫=fú 唯 弗 居 ， 是以 不 去 。",
             "gloss_en": "the ten thousand things / arise / there / and / not / refuse / give life / but / not / "
                         "possess / act / but / not / presume / work / complete / but / not / dwell / "
                         "now / only because / not / dwell / therefore / not / leave"},
        ],
    },
    {
        "id": "p003", "title": "Chapter 3", "zh_title": "第三章",
        "units": [
            {"seg": "不 尚 贤 ， 使 民 不 争 ； 不 贵 难 得 之 货 ， 使 民 不 为=wéi 盗 ； "
                    "不 见=xiàn 可 欲 ， 使 民 心 不 乱 。",
             "gloss_en": "not / exalt / the worthy / make / people / not / contend / not / prize / hard / get / "
                         "(of) / goods / make / people / not / become / thieves / not / display / can / desire / "
                         "make / people / heart / not / be troubled"},
            {"seg": "是以 圣人 之 治 ， 虚 其 心 ， 实 其 腹 ， 弱 其 志 ， 强=qiáng 其 骨 。",
             "gloss_en": "therefore / the sage / 's / governing / empty / their / hearts / fill / their / "
                         "bellies / weaken / their / wills / strengthen / their / bones"},
            {"seg": "常 使 民 无 知 无 欲 。 使 夫=fú 智 者 不 敢 为=wéi 也 。 为=wéi 无为 ， 则 无 不 治 。",
             "gloss_en": "always / make / people / without / knowing / without / desire / make / those / clever / "
                         "ones / not / dare / act / (final) / do / not-doing / then / nothing / not / governed"},
        ],
    },
]

DAODEJING_HEADING_GLOSS = {"第一章": "chapter one", "第二章": "chapter two", "第三章": "chapter three"}

# My English translation (the "final" edition), one string per unit above.
DAODEJING_EN = [
    [
        "A way that can be walked is not the constant Way; a name that can be named is not the constant name.",
        "Nameless, it is the beginning of heaven and earth; named, it is the mother of the ten thousand things.",
        "So, ever without desire, one sees its subtlety; ever with desire, one sees its boundaries.",
        "These two come out together but differ in name; together they are called the dark mystery. "
        "Mystery upon mystery: the gate of all subtleties.",
    ],
    [
        "When everyone under heaven knows beauty as beauty, there is ugliness already; when all know "
        "good as good, there is the not-good already.",
        "So being and non-being give birth to each other, hard and easy complete each other, long and "
        "short shape each other, high and low lean on each other, note and voice answer each other, "
        "before and after follow each other.",
        "Therefore the sage abides in the work of not-doing and practises the teaching without words.",
        "The ten thousand things arise and he does not turn them away; he gives life but does not "
        "possess, acts but does not presume, completes the work but does not dwell on it. Just because "
        "he does not dwell on it, it does not leave him.",
    ],
    [
        "Do not exalt the worthy, and the people will not contend; do not prize goods that are hard to "
        "get, and the people will not turn thieves; do not display what can be desired, and the "
        "people's hearts will not be troubled.",
        "Therefore the sage governs by emptying their hearts and filling their bellies, weakening their "
        "ambitions and strengthening their bones.",
        "He always keeps the people without knowing and without desire, and sees that the clever do "
        "not dare to act. Act by not acting, and nothing will be ungoverned.",
    ],
]

# James Legge, The Texts of Taoism (Sacred Books of the East 39, 1891),
# chapters 1-3; his numbered paragraphs fall on the units above.
DAODEJING_LEGGE = [
    [
        "The Tao that can be trodden is not the enduring and unchanging Tao. The name that can be "
        "named is not the enduring and unchanging name.",
        "(Conceived of as) having no name, it is the Originator of heaven and earth; (conceived of as) "
        "having a name, it is the Mother of all things.",
        "Always without desire we must be found,\nIf its deep mystery we would sound;\n"
        "But if desire always within us be,\nIts outer fringe is all that we shall see.",
        "Under these two aspects, it is really the same; but as development takes place, it receives "
        "the different names. Together we call them the Mystery. Where the Mystery is the deepest is "
        "the gate of all that is subtle and wonderful.",
    ],
    [
        "All in the world know the beauty of the beautiful, and in doing this they have (the idea of) "
        "what ugliness is; they all know the skill of the skilful, and in doing this they have (the "
        "idea of) what the want of skill is.",
        "So it is that existence and non-existence give birth the one to (the idea of) the other; that "
        "difficulty and ease produce the one (the idea of) the other; that length and shortness "
        "fashion out the one the figure of the other; that (the ideas of) height and lowness arise "
        "from the contrast of the one with the other; that the musical notes and tones become "
        "harmonious through the relation of one with another; and that being before and behind give "
        "the idea of one following another.",
        "Therefore the sage manages affairs without doing anything, and conveys his instructions "
        "without the use of speech.",
        "All things spring up, and there is not one which declines to show itself; they grow, and "
        "there is no claim made for their ownership; they go through their processes, and there is "
        "no expectation (of a reward for the results). The work is accomplished, and there is no "
        "resting in it (as an achievement).\nThe work is done, but how no one can see;\n"
        "'Tis this that makes the power not cease to be.",
    ],
    [
        "Not to value and employ men of superior ability is the way to keep the people from rivalry "
        "among themselves; not to prize articles which are difficult to procure is the way to keep "
        "them from becoming thieves; not to show them what is likely to excite their desires is the "
        "way to keep their minds from disorder.",
        "Therefore the sage, in the exercise of his government, empties their minds, fills their "
        "bellies, weakens their wills, and strengthens their bones.",
        "He constantly (tries to) keep them without knowledge and without desire, and where there are "
        "those who have knowledge, to keep them from presuming to act (on it). When there is this "
        "abstinence from action, good order is universal.",
    ],
]

# --------------------------------------------------------------------------
# The Gettysburg Address (the Bliss copy, 1864).
# --------------------------------------------------------------------------

GETTYSBURG = [
    "Four score and seven years ago our fathers brought forth on this continent, a new nation, "
    "conceived in Liberty, and dedicated to the proposition that all men are created equal.",
    "Now we are engaged in a great civil war, testing whether that nation, or any nation so "
    "conceived and so dedicated, can long endure. We are met on a great battle-field of that war. "
    "We have come to dedicate a portion of that field, as a final resting place for those who here "
    "gave their lives that that nation might live. It is altogether fitting and proper that we "
    "should do this.",
    "But, in a larger sense, we can not dedicate—we can not consecrate—we can not hallow—this "
    "ground. The brave men, living and dead, who struggled here, have consecrated it, far above our "
    "poor power to add or detract. The world will little note, nor long remember what we say here, "
    "but it can never forget what they did here. It is for us the living, rather, to be dedicated "
    "here to the unfinished work which they who fought here have thus far so nobly advanced. It is "
    "rather for us to be here dedicated to the great task remaining before us—that from these "
    "honored dead we take increased devotion to that cause for which they gave the last full "
    "measure of devotion—that we here highly resolve that these dead shall not have died in "
    "vain—that this nation, under God, shall have a new birth of freedom—and that government of "
    "the people, by the people, for the people, shall not perish from the earth.",
]
