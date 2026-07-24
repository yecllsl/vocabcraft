# 补存因编号冲突被覆盖的词汇
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from vocabcraft_mcp.tools.crud import save_vocab

missing = [
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
]

saved = []
for v in missing:
    result = save_vocab(v)
    saved.append((v["structured"]["word"], result.get("vocab_id"), result.get("error")))

for word, vid, err in saved:
    if err:
        print(f"  - {word}: 失败 - {err}")
    else:
        print(f"  - {word} -> {vid}")
