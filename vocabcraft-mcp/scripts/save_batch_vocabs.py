# 批量保存图片中解析出的德语词汇
import sys
from pathlib import Path

# 确保 vocabcraft_mcp 在路径中
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from vocabcraft_mcp.tools.crud import save_vocab

vocabs = [
    {
        "structured": {
            "word": "dagegen",
            "part_of_speech": "Adv.",
            "definitions": [
                {"text": "向着这，对此（指前面提到的事情）", "examples": ["Jetzt gibt es noch kein Mittel dafür. 目前对此还没有任何办法。"]},
                {"text": "反对", "examples": ["Er ist prinzipiell dagegen, zu viele Arbeiter anzustellen. 他原则上反对雇佣过多的工人。"]},
                {"text": "与此相反；与此相比", "examples": ["Seine Arbeit ist hervorragend, dagegen ist meine nichts. 他的工作做得非常出色，相比之下我就太差了。"]},
            ],
            "language": "de",
        }
    },
    {
        "structured": {
            "word": "daheim",
            "part_of_speech": "Adv.",
            "definitions": [
                {"text": "在家", "examples": [
                    "bei uns daheim 在我们家乡",
                    "daheim bleiben / sein 在家",
                    "Wie geht es daheim? 你家里人都好吗？",
                ]},
            ],
            "language": "de",
        }
    },
    {
        "structured": {
            "word": "daher",
            "part_of_speech": "Adv.",
            "definitions": [
                {"text": "因此", "examples": ["Er ist krank und kann daher nicht kommen. 他病了，因此不能来。"]},
                {"text": "从那儿（来）", "examples": [
                    "Ich komme gerade daher. 我刚从那儿来。",
                    "Von daher muss der Bus kommen. 公共汽车一定从那儿来。",
                ]},
            ],
            "language": "de",
        }
    },
    {
        "structured": {
            "word": "dahin",
            "part_of_speech": "Adv.",
            "definitions": [
                {"text": "到那儿去", "examples": ["Sie fahren oft dahin. 他们经常坐车到那里去。"]},
                {"text": "到那时为止", "examples": ["Bis dahin muss ich mit der Arbeit fertig sein. 到那时我得把工作做完。"]},
                {"text": "到……程度，到……状况", "examples": ["Lass es nicht dahin kommen! 不能让事情达到这种地步！"]},
            ],
            "language": "de",
        }
    },
    {
        "structured": {
            "word": "dahinter",
            "part_of_speech": "Adv.",
            "definitions": [
                {"text": "在后面", "examples": ["Wenn ich eine Aufgabe erledigt habe, schreibe ich ein X dahinter. 每当我完成一个任务时，我就在后面写一个X。"]},
                {"text": "背后，幕后", "examples": ["Wer steckt denn dahinter? 究竟谁在幕后策划？"]},
            ],
            "language": "de",
        }
    },
    {
        "structured": {
            "word": "damalig",
            "part_of_speech": "Adj.",
            "definitions": [
                {"text": "当时的", "examples": [
                    "die damalige Regierung 当时的政府",
                    "unter den damaligen Umständen 在当时的环境下",
                ]},
            ],
            "language": "de",
        }
    },
    {
        "structured": {
            "word": "da",
            "part_of_speech": "Adv. / Konj.",
            "definitions": [
                {"text": "那儿，这儿", "examples": [
                    "das Gebäude da 那儿的那幢建筑",
                    "Sie ist schon da. 她已经在那儿了。",
                ]},
                {"text": "那时，这时", "examples": ["Ich weiß nicht, ob ich da Zeit habe. 我不知道那时我有没有时间。"]},
                {"text": "在这种情况下", "examples": ["Was kann ich da noch sagen? 在这种情况下我还能说什么呢？"]},
                {"text": "因为，由于", "examples": ["Da sie krank ist, kann sie heute nicht zur Arbeit kommen. 因为她生病了，所以她今天不能来上班。"]},
            ],
            "language": "de",
        }
    },
    {
        "structured": {
            "word": "dabei",
            "part_of_speech": "Adv.",
            "definitions": [
                {"text": "在附近，在这旁边；在场", "examples": [
                    "ein Haus mit einem Garten dabei 一幢带有花园的房子",
                    "Als der Verkehrsunfall geschah, bin ich dabei gewesen. 交通事故发生时我在场。",
                ]},
                {"text": "与此同时，当时", "examples": ["Er sieht fern und raucht dabei eine Zigarette. 他一面看电视，一面抽烟。"]},
            ],
            "language": "de",
        }
    },
    {
        "structured": {
            "word": "Dach",
            "part_of_speech": "n.",
            "definitions": [
                {"text": "屋顶，安全，庇护", "examples": [
                    "ein Dach ausbessern / decken 修理/盖屋顶",
                    "mit jmdm. unter einem Dach leben 和某人在同一屋檐下生活",
                    "kein Dach über dem Kopf haben 没有栖身之地",
                    "etw. (A.) unter Dach und Fach bringen 圆满结束某事",
                ]},
            ],
            "language": "de",
        }
    },
    {
        "structured": {
            "word": "dadurch",
            "part_of_speech": "Adv.",
            "definitions": [
                {"text": "通过（所提到的事或物）", "examples": ["Wir wollen ein Treffen organisieren und dadurch einander näher kennen lernen. 我们想要组织一个聚会，想通过聚会互相增进了解。"]},
                {"text": "因此，由于", "examples": ["Dadurch, dass mein Zug Verspätung hatte, konnte ich nicht rechtzeitig kommen. 由于我坐的火车晚点了，因此我不能及时到达。"]},
            ],
            "language": "de",
        }
    },
    {
        "structured": {
            "word": "dafür",
            "part_of_speech": "Adv.",
            "definitions": [
                {"text": "为此，在这方面，在这件事上", "examples": ["Er ist dafür zuständig, das Projekt durchzuführen. 他负责推进这个项目。"]},
                {"text": "对此", "examples": []},
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
