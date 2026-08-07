"""创建测试用.xlsx文件"""
from pathlib import Path

import openpyxl


def create_test_xlsx():
    """创建测试用.xlsx文件"""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "词汇表"

    # 添加表头
    headers = ["word", "phonetic", "part_of_speech", "definitions", "examples", "language"]
    ws.append(headers)

    # 添加测试数据
    test_data = [
        ["hello", "/həˈloʊ/", "interj.", "你好", "Hello, how are you?", "en"],
        ["hello", "/həˈloʊ/", "interj.", "喂（用于引起注意）", "Hello, is anyone there?", "en"],
        ["world", "/wɜːrld/", "n.", "世界", "The world is beautiful.", "en"],
        ["你好", "", "interj.", "hello", "你好，很高兴见到你。", "zh"],
        ["吃", "", "v.", "eat", "我吃饭。", "zh"],
        ["吃", "", "v.", "have a meal", "我们一起吃吧。", "zh"],
    ]

    for row in test_data:
        ws.append(row)

    # 保存文件
    output_path = Path(__file__).parent / "test_data.xlsx"
    wb.save(output_path)
    print(f"测试文件已创建: {output_path}")

if __name__ == "__main__":
    create_test_xlsx()
