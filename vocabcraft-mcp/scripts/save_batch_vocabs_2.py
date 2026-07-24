# 批量保存第二批德语词汇（42个）
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from vocabcraft_mcp.tools.crud import save_vocab

vocabs = [
    # ========== 第一张图（11个）==========
    {
        "structured": {
            "word": "dazwischen",
            "part_of_speech": "Adv.",
            "definitions": [
                {"text": "（表示地点）在这中间，其中，其间", "examples": [
                    "Zum Schluss gibt man einen Löffel Sahne dazu. 最后再加上一勺奶油。",
                    "Du fährst von Marktplatz bis zum Bahnhof. Dazwischen sind sieben Haltestellen. 你坐车从集市广场到火车站，这中间共有七站。"
                ]},
                {"text": "（表示时间）在这（两段时间）之间，在（中间）这段时间里", "examples": [
                    "Heute habe ich zwei Vorlesungen an der Uni. Dazwischen habe ich zwei Stunden Pause. 今天我在大学有两堂大课，中间有两小时休息。"
                ]},
                {"text": "（指所说的事）在这里面，其中", "examples": [
                    "Wir haben alle Bewerbungen durchgesehen, aber Ihre Bewerbung war nicht dazwischen. 我们看了全部求职信，但您的不在里面。"
                ]},
            ],
            "language": "de",
        }
    },
    {
        "structured": {
            "word": "Debatte",
            "part_of_speech": "f.",
            "definitions": [
                {"text": "辩论，讨论", "examples": [
                    "In der Sitzung kam es zu einer heftigen Debatte. 会上出现了激烈的争论。",
                    "eine Debatte eröffnen / führen / schließen 开始/进行/结束一场辩论"
                ]},
            ],
            "language": "de",
        }
    },
    {
        "structured": {
            "word": "Decke",
            "part_of_speech": "f.",
            "definitions": [
                {"text": "天花板，顶棚", "examples": [
                    "Das Zimmer hat eine hohe Decke. 这房间的天花板高。"
                ]},
                {"text": "覆盖物，套，罩", "examples": [
                    "eine Decke auflegen 铺上一层覆盖物"
                ]},
                {"text": "书皮", "examples": [
                    "die Decke eines Buches 一本书的书皮"
                ]},
            ],
            "language": "de",
        }
    },
    {
        "structured": {
            "word": "decken",
            "part_of_speech": "+ A.",
            "definitions": [
                {"text": "盖，覆盖；铺盖；准备好，摆好", "examples": [
                    "das Dach mit Stroh decken 用稻草盖屋顶",
                    "den Tisch für vier Personen decken 摆放四个人的餐具"
                ]},
                {"text": "满足", "examples": [
                    "den Bedarf der Konsumenten decken 满足消费者的需求"
                ]},
                {"text": "保护，掩护，庇护", "examples": [
                    "Die Mutter hat das Kind mit ihrem Körper gedeckt. 这位母亲用她的身体来保护孩子。"
                ]},
            ],
            "language": "de",
        }
    },
    {
        "structured": {
            "word": "definieren",
            "part_of_speech": "+ A.",
            "definitions": [
                {"text": "下定义，阐明", "examples": [
                    "Wir müssen zuerst definieren, wofür unsere Marke steht. 我们首先需要定义我们的品牌代表了什么？",
                    "Können Sie die Pubertät genau definieren? 您是否能给青春期一个准确的定义？"
                ]},
            ],
            "language": "de",
        }
    },
    {
        "structured": {
            "word": "dein",
            "part_of_speech": "Pron.",
            "definitions": [
                {"text": "你的", "examples": []},
            ],
            "language": "de",
        }
    },
    {
        "structured": {
            "word": "Demokratie",
            "part_of_speech": "f.",
            "definitions": [
                {"text": "民主，民主政体", "examples": [
                    "eine parlamentarische Demokratie 议会制民主政体"
                ]},
            ],
            "language": "de",
        }
    },
    {
        "structured": {
            "word": "demokratisch",
            "part_of_speech": "Adj.",
            "definitions": [
                {"text": "民主的", "examples": [
                    "ein demokratischer Staat 一个民主的国家",
                    "die demokratische Diktatur des Volkes 人民民主专政"
                ]},
            ],
            "language": "de",
        }
    },
    {
        "structured": {
            "word": "demonstrieren",
            "part_of_speech": "(+ A.)",
            "definitions": [
                {"text": "用实例说明；演示", "examples": [
                    "die Arbeitsweise einer neuen Maschine demonstrieren 演示一部新机器的工作方式"
                ]},
                {"text": "举行示威游行", "examples": [
                    "für / gegen etw. (A.) demonstrieren 为支持/反对某事而举行示威游行"
                ]},
            ],
            "language": "de",
        }
    },
    {
        "structured": {
            "word": "denkbar",
            "part_of_speech": "Adj.",
            "definitions": [
                {"text": "可想象的，可设想的", "examples": [
                    "Ohne Luft ist kein Leben denkbar. 没有空气就不可能有生命。",
                    "Ich finde es denkbar, dass wir in einer Woche das Projekt fertig entwerfen können. 我觉得我们一周内能够将项目规划完成，这是可以想象的。"
                ]},
            ],
            "language": "de",
        }
    },
    {
        "structured": {
            "word": "denken",
            "part_of_speech": "(+ A.)",
            "definitions": [
                {"text": "想，思考", "examples": [
                    "logisch / scharf denken 合乎逻辑地/敏锐地思考"
                ]},
                {"text": "想到，认为", "examples": [
                    "Er dachte, dass er diese Arbeit allein erledigen könnte. 他认为他能独自完成这项工作。"
                ]},
                {"text": "想到，考虑到", "examples": [
                    "Denken Sie noch daran? 您还在想这件事吗？",
                    "Der Mensch denkt, Gott lenkt. 谋事在人，成事在天。"
                ]},
            ],
            "language": "de",
        }
    },
    # ========== 第二张图（9个）==========
    {
        "structured": {
            "word": "Definition",
            "part_of_speech": "f.",
            "definitions": [
                {"text": "定义，释义", "examples": [
                    "Leider kannst du die Definition von diesem Fremdwort im Wörterbuch nicht finden. 可惜你在字典里无法找到这个外来词的定义。",
                    "Manche Definitionen sind zweideutig. 有些定义是模棱两可的。"
                ]},
            ],
            "language": "de",
        }
    },
    {
        "structured": {
            "word": "darauf",
            "part_of_speech": "Adv.",
            "definitions": [
                {"text": "一天之后", "examples": [
                    "den Tag darauf 一天之后"
                ]},
                {"text": "在这后面，接着", "examples": [
                    "Kurze Zeit darauf ist er gestorben. 不久以后他去世了。",
                    "Darauf ereignete sich (A.) Folgendes: ... 接着发生了下面的事情：……"
                ]},
                {"text": "因此，因而", "examples": [
                    "Es war ein großer Skandal um die Steuergelder und darauf wurde der Geschäftsführer vor Gericht geklagt. 这是一个巨大的税款丑闻，企业主管因此被被告上法庭。"
                ]},
                {"text": "（指所说的事）对此", "examples": [
                    "Allein darauf kommt es an! 关键就在这里！",
                    "Man muss darauf achten, dass der Fahrplan nur für das Wochenende gilt. 我们必须注意，这张时刻表只适用于周末。"
                ]},
                {"text": "在这上面", "examples": [
                    "darauf liegen / sitzen / stehen 躺/坐/站在上面"
                ]},
                {"text": "此后，然后", "examples": [
                    "Zum Schluss streut man Zucker darauf. 最后在上面撒上糖。"
                ]},
            ],
            "language": "de",
        }
    },
    {
        "structured": {
            "word": "daraufhin",
            "part_of_speech": "Adv.",
            "definitions": [
                {"text": "因此，于是，接着", "examples": [
                    "Der Lieferant wollte den Preis erhöhen, daraufhin änderten wir den Plan. 供应商要提高价格，因此我们改变了计划。"
                ]},
                {"text": "在这后面", "examples": [
                    "Nach dem Sport duscht er zuerst schnell, danach ruht er aus. 很快地淋浴，然后休息。"
                ]},
            ],
            "language": "de",
        }
    },
    {
        "structured": {
            "word": "daraus",
            "part_of_speech": "Adv.",
            "definitions": [
                {"text": "从这里面", "examples": [
                    "Sie öffnete die Tasche und holte daraus ihren Lippenstift. 她打开包，从里面取出她的口红。"
                ]},
                {"text": "由此，从中", "examples": [
                    "Wir müssen Schlussfolgerungen daraus ziehen. 我们必须从中得出结论。",
                    "Daraus ergeben sich viele Möglichkeiten. 由此产生了许多可能性。",
                    "Was soll daraus werden? 事情将会怎样呢？"
                ]},
            ],
            "language": "de",
        }
    },
    {
        "structured": {
            "word": "darin",
            "part_of_speech": "Adv.",
            "definitions": [
                {"text": "在这里面", "examples": [
                    "Hast du den Artikel gelesen? Es gibt viele neue Forschungsergebnisse darin. 你看了这篇文章吗？里面有许多新的研究成果。"
                ]},
                {"text": "（指所说的事）在这件事上", "examples": [
                    "sich (A.) darin irren, in 在这点上搞错"
                ]},
            ],
            "language": "de",
        }
    },
    {
        "structured": {
            "word": "Darstellung",
            "part_of_speech": "f.",
            "definitions": [
                {"text": "描述，描写，阐述", "examples": [
                    "Das Buch hat die Darstellung eines Politikers zum Inhalt. 这本书的内容是描写一位政治家。"
                ]},
                {"text": "表现，表达", "examples": [
                    "Seine Darstellung klingt sehr unwahrscheinlich. 他的说明听起来极不可信。"
                ]},
                {"text": "扮演，演出", "examples": [
                    "In diesem Film ist die Darstellung der Nebenrolle ausgezeichnet. 在这部影片中，配角的表演十分出色。"
                ]},
            ],
            "language": "de",
        }
    },
    {
        "structured": {
            "word": "darüber",
            "part_of_speech": "Adv.",
            "definitions": [
                {"text": "在这上面", "examples": [
                    "ein Buch darüber legen 在这上面放本书",
                    "Wasser darüber gießen 把水浇在上面"
                ]},
                {"text": "对此，关于这个", "examples": [
                    "Es gab einen Einbruch bei Familie Müller. Die ganze Nachbarschaft spricht jetzt darüber. 穆勒家发生了盗窃案，现在所有的邻居都在谈论这事。",
                    "darüber hinaus 此外"
                ]},
            ],
            "language": "de",
        }
    },
    {
        "structured": {
            "word": "darum",
            "part_of_speech": "Adv.",
            "definitions": [
                {"text": "在这周围", "examples": [
                    "Er hat sich (D.) den Finger verletzt und klebt nun ein Pflaster darum. 他把手指弄伤了，现在裹上了一块创可贴。"
                ]},
                {"text": "因此，所以", "examples": [
                    "Sie ist sehr krank, darum kann sie nicht zur Veranstaltung kommen. 她病得很重，所以不能来参加活动。"
                ]},
                {"text": "对此，为此", "examples": [
                    "Der junge Mann bittet seine Eltern darum, dass sie sich (A.) um die Kinder kümmern. 这名年轻男子请求他的父母照顾孩子们。",
                    "Darum geht es ja gerade! 问题就在这里。",
                    "Es handelt sich darum, ob ... 问题在于，是否……"
                ]},
            ],
            "language": "de",
        }
    },
    {
        "structured": {
            "word": "darunter",
            "part_of_speech": "Adv.",
            "definitions": [
                {"text": "在这下面", "examples": [
                    "Wir wohnen im ersten Stock, darunter ist ein Laden. 我们住在二楼，下面是一家商店。"
                ]},
            ],
            "language": "de",
        }
    },
    # ========== 第三张图（11个）==========
    {
        "structured": {
            "word": "damals",
            "part_of_speech": "Adv.",
            "definitions": [
                {"text": "当时，那时", "examples": [
                    "Damals war er noch jung. 那时他还年轻。"
                ]},
            ],
            "language": "de",
        }
    },
    {
        "structured": {
            "word": "Dame",
            "part_of_speech": "f.",
            "definitions": [
                {"text": "女士，夫人；（贵）妇人", "examples": [
                    "Meine Damen und Herren! 女士们，先生们！",
                    "die erste Dame des Staates 第一夫人，总统夫人"
                ]},
            ],
            "language": "de",
        }
    },
    {
        "structured": {
            "word": "damit",
            "part_of_speech": "Adv. / Konj.",
            "definitions": [
                {"text": "对此，以此", "examples": [
                    "Er nimmt den Schlüssel und öffnet damit den Koffer. 他拿了钥匙，并以此打开了箱子。"
                ]},
                {"text": "为了，以便", "examples": [
                    "Der Präsident hielt eine Rede, und damit endete die Sitzung. 主席讲了话，会议到此结束。",
                    "Er notiert das Datum, damit er es nicht vergisst. 他为了不忘记而记下日期。"
                ]},
            ],
            "language": "de",
        }
    },
    {
        "structured": {
            "word": "dann",
            "part_of_speech": "Adv.",
            "definitions": [
                {"text": "然后", "examples": [
                    "Und was dann? 然后呢？（后来发生了什么事？）",
                    "Er muss zuerst seine Freundin vom Bahnhof abholen und dann gehen sie zusammen zu seinen Eltern. 他必须先从火车站接他的女朋友，然后再一起去他父母那里。"
                ]},
                {"text": "回头见", "examples": [
                    "Bis dann. 回头见！"
                ]},
                {"text": "那么", "examples": [
                    "Erst wägen, dann wagen. 三思而后行。",
                    "Wenn Sie Hilfe brauchen, dann sagen Sie es mir. 如果您需要帮助，那就告诉我。",
                    "Wenn du morgen nicht kommst, dann gehe ich zu dir. 如果你明天不来，那么我到你这里来。"
                ]},
            ],
            "language": "de",
        }
    },
    {
        "structured": {
            "word": "danken",
            "part_of_speech": "+ D.",
            "definitions": [
                {"text": "感谢，道谢", "examples": [
                    "Ich danke Ihnen für Ihre Hilfe. 我感谢您的帮助。"
                ]},
            ],
            "language": "de",
        }
    },
    {
        "structured": {
            "word": "danke",
            "part_of_speech": "Interj.",
            "definitions": [
                {"text": "谢谢", "examples": [
                    "— Wollen Sie mitfahren? — Danke, nein. — 您要搭车一起走吗？— 不了，谢谢。",
                    "Ich bin dir sehr dankbar dafür, dass du mir in Not geholfen hast. 我非常感激你在困境中帮助了我。"
                ]},
            ],
            "language": "de",
        }
    },
    {
        "structured": {
            "word": "danach",
            "part_of_speech": "Adv.",
            "definitions": [
                {"text": "此后，然后，接着", "examples": [
                    "Nach dem Sport duscht er zuerst schnell, danach ruht er aus. 很快地淋浴，然后休息。"
                ]},
                {"text": "在这后面", "examples": [
                    "Beim Radrennen hielten fünf Fahrer die Spitze, danach folgte das Hauptfeld. 在自行车比赛时，五个运动员骑在最前面，其它运动员跟在后面。"
                ]},
            ],
            "language": "de",
        }
    },
    {
        "structured": {
            "word": "daran",
            "part_of_speech": "Adv.",
            "definitions": [
                {"text": "在这旁边，紧靠着；在这上面", "examples": [
                    "Vergiss nicht, ein paar Briefmarken bei der Post zu kaufen, wenn du daran vorbeikommst. 你从邮局旁边经过时，不要忘记买些邮票。",
                    "etw. (A.) daran kleben 把某物粘上去"
                ]},
                {"text": "正要，接着", "examples": [
                    "Der Direktor hielt eine Rede, daran schloss sich das Sportfest. 校长发言，接着运动会开始。"
                ]},
                {"text": "（指所说的事）对此，对这一点", "examples": [
                    "Jetzt bist du endlich daran. 现在终于轮到你了。",
                    "Achtsamkeit / Respekt davor haben 对此表示尊重"
                ]},
                {"text": "轮到，挨到", "examples": [
                    "Das Kind ist daran gewöhnt, sich (D.) regelmäßig die Zähne zu putzen. 这孩子已习惯按时刷牙。"
                ]},
            ],
            "language": "de",
        }
    },
    {
        "structured": {
            "word": "davor",
            "part_of_speech": "Adv.",
            "definitions": [
                {"text": "（表示地点）在这前面", "examples": [
                    "ein Haus mit zwei Bäumen davor 前面有两棵树的房屋",
                    "Dort ist der Notausgang. Davor darf man keine Autos parken. 那里是紧急出口，前面不允许停车。"
                ]},
                {"text": "在这以前", "examples": [
                    "Die Filmpremiere beginnt heute Abend um 8 Uhr, davor findet eine Pressekonferenz statt. 今晚电影首映式八点开始，之前将举行记者招待会。"
                ]},
                {"text": "（指所说的事）对此", "examples": [
                    "Ich habe sie davor gewarnt, dass man dem Typ nicht vertrauen kann. 我警告过她，不要相信这个家伙。"
                ]},
            ],
            "language": "de",
        }
    },
    {
        "structured": {
            "word": "dankbar",
            "part_of_speech": "Adj.",
            "definitions": [
                {"text": "感谢的，感激的", "examples": [
                    "Gott sei Dank! 谢天谢地！",
                    "Vielen Dank! 多谢！",
                    "jmdm. seinen Dank ausdrücken / aussprechen 向某人表示感谢",
                    "etw. (A.) mit Dank annehmen / erhalten 怀着谢意接受/收到某物"
                ]},
            ],
            "language": "de",
        }
    },
    {
        "structured": {
            "word": "Dank",
            "part_of_speech": "m.",
            "definitions": [
                {"text": "感谢", "examples": [
                    "jmdm. für etw. (A.) Dank sagen 为某事向某人道谢"
                ]},
            ],
            "language": "de",
        }
    },
    # ========== 第四张图（11个）==========
    {
        "structured": {
            "word": "das",
            "part_of_speech": "Art. / Pron.",
            "definitions": [
                {"text": "这个", "examples": []},
            ],
            "language": "de",
        }
    },
    {
        "structured": {
            "word": "dass",
            "part_of_speech": "Konj.",
            "definitions": [
                {"text": "（引导主语从句、宾语从句、定语从句、目的从句等）", "examples": [
                    "Damals wusste ich nicht, dass er schon gegangen ist. 当时我不知道他已经走了。",
                    "Ein interessantes Ergebnis der Untersuchungen ist, dass bei vielen Männern diese Seite leer bleibt. 这些调查的一项有趣的结果是，许多男人把这一页空着。"
                ]},
            ],
            "language": "de",
        }
    },
    {
        "structured": {
            "word": "Datei",
            "part_of_speech": "f.",
            "definitions": [
                {"text": "资料档案，文件", "examples": [
                    "Heutzutage kann man die Dateien online speichern. 现在人们可以在网上保存资料数据。"
                ]},
            ],
            "language": "de",
        }
    },
    {
        "structured": {
            "word": "Datum",
            "part_of_speech": "n.",
            "definitions": [
                {"text": "日期", "examples": [
                    "das Datum angeben / ändern 注明/改变日期",
                    "Welches Datum ist heute? 今天几号？"
                ]},
                {"text": "资料，数据", "examples": [
                    "die technischen Daten einer Maschine 一部机器的技术数据",
                    "Daten sammeln / verwerten 搜集/利用数据"
                ]},
            ],
            "language": "de",
        }
    },
    {
        "structured": {
            "word": "Dauer",
            "part_of_speech": "f.",
            "definitions": [
                {"text": "期限，（持续）时间", "examples": [
                    "die Dauer ihres Aufenthalts 她逗留的时间",
                    "Dieser Pass gilt für die Dauer von zehn Jahren. 这本护照的有效期是十年。",
                    "auf die Dauer 长时间地，长此以往",
                    "nicht von langer Dauer sein / nur von kurzer Dauer sein 不能长久存在，不能持久"
                ]},
            ],
            "language": "de",
        }
    },
    {
        "structured": {
            "word": "dauerhaft",
            "part_of_speech": "Adj.",
            "definitions": [
                {"text": "坚固的，耐用的，经久不变的，持久的", "examples": [
                    "Der Kleber verbindet zwei Glasflächen dauerhaft miteinander. 胶水将两个玻璃面牢固地粘在一起。"
                ]},
            ],
            "language": "de",
        }
    },
    {
        "structured": {
            "word": "dauern",
            "part_of_speech": "—",
            "definitions": [
                {"text": "持续，历时", "examples": [
                    "Wie lange dauert diese Sitzung? 这个会议持续多久？",
                    "Seine Reise nach Europa hat zwei Wochen gedauert. 他的欧洲之旅持续了两周。"
                ]},
            ],
            "language": "de",
        }
    },
    {
        "structured": {
            "word": "davon",
            "part_of_speech": "Adv.",
            "definitions": [
                {"text": "从那儿，离那儿", "examples": [
                    "Hände davon weg! 别碰它！",
                    "Die Post liegt nicht weit davon. 邮局离那儿不远。"
                ]},
                {"text": "由此", "examples": [
                    "Er hat sich (A.) an der Tischkante gestoßen und davon einen blauen Fleck bekommen. 他撞在桌角上，起了一块紫斑。",
                    "Das kommt davon! 这是自作自受！"
                ]},
                {"text": "（指所说的事）关于此事，对此", "examples": [
                    "Wie ist der Unfall passiert? Ich habe davon gar nichts gehört. 事故是怎么发生的？我完全没有听说此事。"
                ]},
                {"text": "从中，其中", "examples": [
                    "Wer will noch etwas davon? 谁还想要一点（吃的东西等）？",
                    "Der Sportverein hat insgesamt 200 Mitglieder, davon sind nur 40 Frauen. 这一运动俱乐部一共有200名成员，其中仅有40名女性。"
                ]},
            ],
            "language": "de",
        }
    },
    {
        "structured": {
            "word": "davor",
            "part_of_speech": "Adv.",
            "definitions": [
                {"text": "（表示地点）在这前面", "examples": [
                    "ein Haus mit zwei Bäumen davor 前面有两棵树的房屋",
                    "Dort ist der Notausgang. Davor darf man keine Autos parken. 那里是紧急出口，前面不允许停车。"
                ]},
                {"text": "在这以前", "examples": [
                    "Die Filmpremiere beginnt heute Abend um 8 Uhr, davor findet eine Pressekonferenz statt. 今晚电影首映式八点开始，之前将举行记者招待会。"
                ]},
                {"text": "（指所说的事）对此", "examples": [
                    "Ich habe sie davor gewarnt, dass man dem Typ nicht vertrauen kann. 我警告过她，不要相信这个家伙。"
                ]},
            ],
            "language": "de",
        }
    },
    {
        "structured": {
            "word": "dazu",
            "part_of_speech": "Adv.",
            "definitions": [
                {"text": "（表示目的）为此", "examples": [
                    "Er wollte jetzt Deutsch lernen. Dazu besucht er jedes Wochenende einen Deutschkurs. 他现在想要学习德语，为此每周末去上德语课程。"
                ]},
                {"text": "（指所说的话）对此", "examples": [
                    "Das Kind hat keine Lust dazu. 孩子对此没有兴趣。",
                    "Das ist unser neuer Plan. Was sagst du dazu? 这是我们的新计划，你对此有什么意见吗？"
                ]},
            ],
            "language": "de",
        }
    },
    {
        "structured": {
            "word": "daneben",
            "part_of_speech": "Adv.",
            "definitions": [
                {"text": "在这边上", "examples": [
                    "Mein Büro liegt daneben. 我的办公室就在边上。"
                ]},
                {"text": "此外，其次；同时", "examples": [
                    "In der Vorlesung müssen wir daneben noch über andere Umweltprobleme diskutieren. 此外，我们在课上还要对其他环境问题进行讨论。"
                ]},
                {"text": "（指所说的事）在这件事上", "examples": [
                    "sich (A.) daran irren, in 在这点上搞错"
                ]},
            ],
            "language": "de",
        }
    },
]

saved = []
errors = []
for v in vocabs:
    result = save_vocab(v)
    if "error" in result:
        errors.append((v["structured"]["word"], result["error"]))
    else:
        saved.append((v["structured"]["word"], result["vocab_id"]))

print(f"成功保存 {len(saved)} 个词汇:")
for word, vid in saved:
    print(f"  - {word} -> {vid}")

if errors:
    print(f"\n失败 {len(errors)} 个:")
    for word, err in errors:
        print(f"  - {word}: {err}")
