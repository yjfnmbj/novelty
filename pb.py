#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
pb.py - 中文文本格式化处理脚本（专为小说、文档排版优化）
================================================================================

【功能概述】
对中文小说、长文档进行专业级排版处理，输出美观、规范、适合阅读的纯文本。
脚本会自动完成标点规范化、段落整理、标题识别、字数统计、分隔符美化等一系列工作，
并提供两种输出模式（默认首行缩进模式与智能换行模式），同时保持高度幂等性。

【核心特性详解】

1. 标点符号与字符规范化
   - 半角标点自动转为全角（, . ! ? ; : ( ) " ' 等 → ，。！？；：（）「『等）
   - 连续标点智能合并：多个句号/省略号 → ……，多个破折号 → ——
   - 英文与数字全角字符自动转为半角（ＡＢＣ → ABC，１２３ → 123）
   - 破折号、省略号、波浪线等特殊符号统一规范

2. 智能段落分割与格式化
   - 按句子结束标点（。！？…」等）+ 换行进行逻辑段落切分
   - 默认模式：正文每段自动添加首行全角缩进（　　），续行无缩进
   - -l N 智能换行模式：
     • 章节标题自动居中（使用全角空格 '　' 填充两侧）
     • 正文段落首行缩进 + 续行无缩进
     • 智能处理行首禁则（避免 ，。！？等单独成行）
     • 支持双标点（…… ——）单独成短行
     • 标题与正文之间自动插入空行分隔
     • 整体行宽可控（推荐 35~50 字符）

3. 章节与小节标题自动识别
   - 精准识别常见标题格式：
     第X章、第X卷、第X集、第X部
     （1）、（一）、（数字）等小节标题
   - 标题后可自动追加该章字数统计（本章字数：XXXX）
   - 可通过 -n / --no-wordcount 参数关闭字数追加

4. 字数统计（纯净正文）
   - 自动在文件开头输出「总字数：XXXX」
   - 每个识别到的章节标题后追加「（本章字数：XXXX）」
   - 统计时自动排除所有空白字符（包括用于排版的全角空格 '　'）
   - 统计范围为标题之后至下一个标题（或文末）之间的实际正文内容

5. 配对标点符号检测与报告
   - 自动检查常见配对标点是否成对：
     「」 『』 《》 【】 （） () "" '' “” ‘’
   - 检测数量不匹配，并定位具体行号及上下文（用【】高亮问题位置）
   - 检查嵌套是否正确（使用栈模拟，报告多余右标点或未闭合左标点）
   - 检查结果以警告形式打印到控制台，不修改原文件内容

6. 引号、括号与空格特殊处理
   - 自动删除「」或（）内部的换行符，实现引号内内容合并
   - 「」之间的多余空白替换为单个换行
   - 保留英文字母/数字后的正常空格，删除其他多余空白字符
   - 全角空格等排版用空白在字数统计时被正确排除

7. 分隔符（*** ***）识别与美化
   - 自动识别各种形式的分隔行（由 * 、※ 、　 、空格等组成的星号行，或单独的 … 行）
   - 将其统一替换为美化的标准分隔符：
     ＊＊＊　＊＊＊　＊＊＊　＊＊＊　＊＊＊

8. ■ 后记/附录保留机制
   - 查找文本中**最后一个** ■ 符号
   - ■ 之前的内容作为正文进行完整排版处理（标点、换行、标题、字数等全部生效）
   - ■ 之后的内容（通常为后记、作者的话、备注、版权声明等）**原样保留**，不做任何修改
   - 最终输出时在排版后的正文末尾直接追加 ■ + 后记内容

9. 其他特性
   - 高度幂等性：无论输入是否已处理过、是否包含旧字数标注，多次运行结果完全一致
   - 强制输出 UTF-8 编码 + Unix 换行符（\n）
   - 无任何外部依赖，仅使用标准库（re、os、sys）
   - 配对标点检查、字数统计、标题识别等功能均可独立理解与扩展

【使用方法】
python pb.py <input.txt> [output.txt] [-l N] [--no-wordcount | -n]

参数说明：
  input.txt          必选，待处理的 UTF-8 文本文件（可含全半角混杂、旧标注、各种格式）
  output.txt         可选，输出文件名。默认在 input 同目录生成 input=.txt（注意等号）
  -l N               可选，启用智能换行模式，N 为每行最大字符数（推荐 35~50）
                     效果见上文“智能换行模式”描述
  --no-wordcount, -n 可选，关闭章节标题后的字数统计（本章字数），仅进行格式化处理

示例：
  python pb.py novel.txt                           # 默认模式，生成 novel=.txt，带总字数和章节字数
  python pb.py novel.txt formatted.txt -l 40       # 智能换行模式（40字/行），带字数统计
  python pb.py novel.txt -n                        # 默认模式，不添加章节字数统计
  python pb.py novel.txt out.txt -l 45 -n          # 智能换行 + 关闭章节字数统计

【注意事项】
- 输入输出均为 UTF-8 编码，强制使用 Unix 换行符（\n）
- 脚本具有高度幂等性，建议直接使用输出文件，无需担心重复运行会损坏内容
- 配对标点检查结果仅打印到控制台（警告性质），不会修改输出文件
- 如需自定义更多规则，可修改脚本顶部的 FORBIDDEN_START_PUNCTS、FORBIDDEN_END_PUNCTS、
  DOUBLE_PUNCTS 等常量
- 本脚本为纯文本处理工具，专注于排版美化，不依赖任何第三方库

版本：2026-06 全面特性版
================================================================================
"""

import re
import os


def check_paired_punctuation(text):
    """
    检测配对标点符号的数量是否一致，并找出不配对的具体位置。
    支持的配对： 「」 『』 《》 【】 （） () "" '' “” ‘’
    同时检查嵌套是否正确（栈匹配，报告多余右标点或未闭合左标点）。
    """
    # 定义需要检查的配对标点（左:右）
    paired_punctuations = {
        '「」': ('「', '」'),
        '『』': ('『', '』'),
        '《》': ('《', '》'),
        '【】': ('【', '】'),
        '（）': ('（', '）'),
        '()': ('(', ')'),
        '""': ('"', '"'),
        "''": ("'", "'"),
        '“”': ('“', '”'),
        '‘’': ('‘', '’')
    }

    results = []
    detailed_warnings = []

    for pair_name, (left, right) in paired_punctuations.items():
        left_count = text.count(left)
        right_count = text.count(right)

        if left_count != right_count:
            results.append(
                f"警告: {pair_name} 数量不匹配 - 左{left}: {left_count}个, 右{right}: {right_count}个"
            )
            # 找出不配对的具体位置及上下文
            if left_count > right_count:
                find_extra_punctuations(text, left, right, pair_name, '左', detailed_warnings)
            else:
                find_extra_punctuations(text, right, left, pair_name, '右', detailed_warnings)
        # else: 数量匹配则静默（可取消注释下方以显示正常信息）
        # results.append(f"正常: {pair_name} 数量匹配 - 各{left_count}个")

    # 检查嵌套是否正确
    check_nesting(text, detailed_warnings)

    all_results = results + detailed_warnings
    return "\n".join(all_results)


def find_extra_punctuations(text, main_char, paired_char, pair_name, side, warnings):
    """
    辅助函数：找出多余的标点符号及其上下文（前后各约10字符），并用【】高亮问题位置。
    """
    positions = [i for i, char in enumerate(text) if char == main_char]

    for pos in positions:
        if not has_proper_pair(text, pos, main_char, paired_char, side):
            start = max(0, pos - 10)
            end = min(len(text), pos + 11)
            context = text[start:end]
            # 标记问题位置
            if start < pos:
                marked_context = context[:pos - start] + '【' + context[pos - start] + '】' + context[pos - start + 1:]
            else:
                marked_context = '【' + context[0] + '】' + context[1:]
            warnings.append(f"  位置: 第{count_lines(text, pos)}行附近 - '{marked_context}'")


def has_proper_pair(text, pos, main_char, paired_char, side):
    """
    检查该标点是否真正“多余”（即没有正确配对的另一半）。
    考虑了简单嵌套情况（中间不能再出现同类左/右标点）。
    """
    if side == '左':
        next_right = text.find(paired_char, pos + 1)
        if next_right != -1:
            between_text = text[pos + 1:next_right]
            if main_char not in between_text:
                return True
    else:
        prev_left = text.rfind(paired_char, 0, pos)  # 注意这里用 paired_char 其实是 left
        if prev_left != -1:
            between_text = text[prev_left + 1:pos]
            if main_char not in between_text:
                return True
    return False


def check_nesting(text, warnings):
    """
    检查常见中文书名/引号的嵌套是否正确（使用栈模拟）。
    目前检查：「」 『』 《》
    """
    check_specific_nesting(text, '「', '」', '「」', warnings)
    check_specific_nesting(text, '『', '』', '『』', warnings)
    check_specific_nesting(text, '《', '》', '《》', warnings)


def check_specific_nesting(text, left_char, right_char, pair_name, warnings):
    """
    具体嵌套检查实现：用栈记录左标点位置，遇到右标点则弹栈。
    栈非空时遇到右标点 → 多余右标点；处理完后栈非空 → 未闭合左标点。
    """
    stack = []
    for i, char in enumerate(text):
        if char == left_char:
            stack.append(i)
        elif char == right_char:
            if stack:
                stack.pop()
            else:
                # 多余的右标点
                start = max(0, i - 10)
                end = min(len(text), i + 11)
                context = text[start:end]
                marked_context = context[:i - start] + '【' + context[i - start] + '】' + context[i - start + 1:]
                warnings.append(
                    f"嵌套错误: {pair_name} 有多余的右标点 - 第{count_lines(text, i)}行: '{marked_context}'"
                )

    # 栈中剩余 → 未闭合的左标点
    for pos in stack:
        start = max(0, pos - 10)
        end = min(len(text), pos + 11)
        context = text[start:end]
        marked_context = context[:pos - start] + '【' + context[pos - start] + '】' + context[pos - start + 1:]
        warnings.append(
            f"嵌套错误: {pair_name} 有未闭合的左标点 - 第{count_lines(text, pos)}行: '{marked_context}'"
        )


def count_lines(text, position):
    """计算某个字符位置对应的行号（从1开始）。"""
    return text[:position].count('\n') + 1


def is_chapter_title(text):
    """
    判断一个逻辑块是否为章节/小节标题。
    支持格式：第X章、第X卷、第X集、第X部、（1）、（一）、（数字）等。
    严格匹配开头，避免误判正文中的“第二章开始...”之类。
    """
    text = text.strip()
    if not text:
        return False
    pattern = r'^(?:第[0123456789零一二三四五六七八九十百千\d]+[章卷集部]|（[0123456789一二三四五六七八九十百千]+）)'
    return bool(re.match(pattern, text))


def center_title(title, width):
    """
    将标题居中（使用全角空格 '　' 填充两侧）。
    如果标题本身已 >= width，则原样返回。
    """
    title = title.strip()
    if not title:
        return ''
    title_len = len(title)
    if title_len >= width:
        return title
    padding = (width - title_len) // 2
    return '　' * padding + title


# 常量定义
FORBIDDEN_START_PUNCTS = {'。', '？', '！', '，', '；', '：', '、'}  # 禁止单独成行的标点（行首禁则）
DOUBLE_PUNCTS = {'……', '——', '———', '…'}  # 可单独成短行的双标点
FORBIDDEN_END_PUNCTS = {'「', '『', '“', '‘', '《', '【', '（', '(', '"', "'", '<', '〈'}  # 行末禁止开引号/开括号等（避免截断内容导致行末出现这些标记，推到下行首，更符合现代中文排版禁则）

# 用于字数统计时排除的空白（包括全角空格 '　'），确保排版补位的空格不计入正文字数
WORD_COUNT_WHITESPACE = r'[\s　]+'


def wrap_body_paragraph(para_text, width):
    """
    将正文段落智能换行到 <= width 字符。
    - 仅第一行添加首行缩进 '　　'
    - 续行无缩进
    - 句尾标点换行时：若下一行会以单个 FORBIDDEN_START_PUNCTS 开头，则“拉回”当前行（允许超宽1字符）
    - 新增行末控制：若当前行末尾为 FORBIDDEN_END_PUNCTS（「『“‘《【等开标记），则本行少1字符，将该标记推到下行行首（更贴近现代中文排版禁则，避免行末截断开引号）
    - 双标点（…… ——）允许单独成短行
    - 整个段落若仅为双标点，则作为短行输出（无缩进）
    """
    stripped = para_text.strip()
    if not stripped:
        return []
    if stripped in DOUBLE_PUNCTS:
        return [stripped]

    indent = '　　'
    first_max = width - len(indent) if width > len(indent) else width
    lines = []
    text = para_text
    i = 0
    n = len(text)
    is_first_line = True
    while i < n:
        if is_first_line:
            max_len = first_max
            prefix = indent
            is_first_line = False
        else:
            max_len = width
            prefix = ''
        j = min(i + max_len, n)
        # 标点处理：允许双标点开头新行；单个禁用标点则拉回当前行
        if j < n:
            next_char = text[j]
            is_double_start = False
            if j + 1 < n:
                two_chars = text[j:j + 2]
                if two_chars in DOUBLE_PUNCTS or (next_char in {'…', '—'} and text[j + 1] in {'…', '—'}):
                    is_double_start = True
            if is_double_start:
                pass  # 允许双标点开头新行
            elif next_char in FORBIDDEN_START_PUNCTS:
                if (j - i) + 1 <= max_len + 1:
                    j += 1  # 拉回标点

        # 行末禁则控制（类似行首禁则的拉回逻辑）
        # 如果当前 chunk 的末尾字符是开引号/开括号等（FORBIDDEN_END_PUNCTS），
        # 说明此处截断会导致行末出现“明显不完整的内容开始标记”，则主动少取1字符，
        # 将该标记推到下一行行首，更符合现代中文书籍排版习惯（避免行末孤立开引号）。
        if j > i + 1:  # 至少保留2字符，避免产生过短行或空行
            end_char = text[j - 1]
            if end_char in FORBIDDEN_END_PUNCTS:
                j -= 1  # 本行少1字符，标记移至下行
        chunk = text[i:j]
        lines.append(prefix + chunk)
        i = j
    return lines


def add_chapter_word_counts(text):
    """
    在每个章节/小节标题后追加该章总字数统计。
    格式：第X章 标题名（本章字数：1234）
    字数 = 该标题后至下一个标题（或文末）之间的正文内容（去除所有空白字符后的长度）。

    【重要】本函数具有完全幂等性：
    - 先全局移除所有旧的“（本章字数：\\d+）”标注（不破坏后续换行符）
    - 然后基于纯正文重新计算并添加新标注
    - 因此无论输入是否已处理过，输出结果一致，且字数准确（不含辅助内容）
    """
    if not text:
        return text

    # 移除所有已有的字数统计标注（包括孤立出现的情况）
    # 只移除标注本身，保留周围的换行/空格，避免破坏标题前的空行结构
    text = re.sub(r'（本章字数：\d+）', '', text)

    # 匹配行首或换行后的标题（支持第X章/卷/集/部 和 （数字） 两种形式）
    # 限制标题后最多80个非特殊字符，避免吃掉太多正文
    pattern_str = (
        r'(?:^|(?<=\n))'
        r'((?:第[0123456789零一二三四五六七八九十百千\d]+[章卷集部]|'
        r'（[0123456789一二三四五六七八九十百千]+）)[^「『《（\n\r]{0,80})'
    )
    pattern = re.compile(pattern_str)

    matches = list(pattern.finditer(text))
    if not matches:
        return text

    # 严格过滤：只保留真正符合 is_chapter_title 的（避免正文中“第二章开始”之类误匹配）
    valid_matches = [m for m in matches if is_chapter_title(m.group(1))]
    if not valid_matches:
        return text

    result_parts = []
    last_end = 0
    for i, match in enumerate(valid_matches):
        start, end = match.span()
        if start > last_end:
            result_parts.append(text[last_end:start])

        title = match.group(1)
        if i + 1 < len(valid_matches):
            content_end = valid_matches[i + 1].start()
        else:
            content_end = len(text)

        chapter_content = text[end:content_end]
        # 统计字数：去除所有空白字符（包括 \s 和全角空格 '　'，确保排版补位的空格不计入正文字数）
        word_count = len(re.sub(WORD_COUNT_WHITESPACE, '', chapter_content))
        new_title = f"{title}（本章字数：{word_count}）"
        result_parts.append(new_title)
        last_end = end

    result_parts.append(text[last_end:])
    return ''.join(result_parts)


def add_newline_after_chapter(text):
    """
    在章节标题（第X章 / （数字））前后插入 __NEWLINE__ 占位符。
    后续会被替换为真实 \n ，并配合 ensure_blank_line_before_titles() 保证标题前后有空行。
    支持扩展形式如「（1）·标题名称」。
    """
    pattern_str = (
        r'((?:第[0123456789零一二三四五六七八九十百千\d]+[章卷集部]|'
        r'（[0123456789一二三四五六七八九十百千]+）)[^「『《（\n\r]{0,80})'
    )
    pattern = re.compile(pattern_str)

    # 第一步：用占位符包裹标题（前后各一个 __NEWLINE__）
    result = pattern.sub(r'__NEWLINE__\1__NEWLINE__', text)

    # 第二步：清理标题后可能残留的多余空白（把 \s*\n\s* 规范为 \n\n）
    # 注意：此步在有 __NEWLINE__ 的情况下可能部分不匹配，但不影响最终结果
    result = re.sub(pattern_str + r'\s*\n\s*', r'\1\n\n', result)

    return result


def replace_spaces_except_after_letters(text):
    """
    删除除英文/数字字母后的空格之外的所有空白字符（保留英文字母后的正常空格）。
    例如： "Hello World中文" -> "Hello World中文"（只保留 Hello 后的空格）
    """
    marker = '__SPACE__'
    text = re.sub(r'(?<=[a-zA-Z]) ', marker, text)  # 临时保护英文字母后的空格
    text = re.sub(r'[^\S\n]+', '', text)            # 删除其他所有空白（保留 \n）
    text = text.replace(marker, ' ')
    return text


def remove_newlines_in_brackets(text):
    """
    删除「」或（）内部的换行符（用于合并引号/括号内的多行内容）。
    注意：如果原文括号不配对，可能导致错误合并（当前实现有长度限制 999 字符）。
    """
    pattern = re.compile(r'(「(.{1,999}?)」|（(.{1,999}?)）)', re.DOTALL)

    def replace_newlines(match):
        content = match.group(2) if match.group(2) is not None else match.group(3)
        if content is not None:
            content = content.replace('\n', '')
            return f'「{content}」' if match.group(2) is not None else f'（{content}）'
        return match.group()

    return pattern.sub(replace_newlines, text)


def replace_whitespace_in_brackets(text):
    """
    将」「之间的空白字符（包括换行）替换为单个换行符。
    例如：」   「 -> 」\n「
    """
    pattern = r'」\s*「'
    return re.sub(pattern, '」\n「', text)


def fullwidth_to_halfwidth(text):
    """
    将全角英文字母和数字转换为半角（A-Z a-z 0-9）。
    其他全角字符（如标点）保持不变。
    """
    fullwidth_to_halfwidth_dict = {
        'Ａ': 'A', 'Ｂ': 'B', 'Ｃ': 'C', 'Ｄ': 'D', 'Ｅ': 'E', 'Ｆ': 'F', 'Ｇ': 'G',
        'Ｈ': 'H', 'Ｉ': 'I', 'Ｊ': 'J', 'Ｋ': 'K', 'Ｌ': 'L', 'Ｍ': 'M', 'Ｎ': 'N',
        'Ｏ': 'O', 'Ｐ': 'P', 'Ｑ': 'Q', 'Ｒ': 'R', 'Ｓ': 'S', 'Ｔ': 'T', 'Ｕ': 'U',
        'Ｖ': 'V', 'Ｗ': 'W', 'Ｘ': 'X', 'Ｙ': 'Y', 'Ｚ': 'Z',
        'ａ': 'a', 'ｂ': 'b', 'ｃ': 'c', 'ｄ': 'd', 'ｅ': 'e', 'ｆ': 'f', 'ｇ': 'g',
        'ｈ': 'h', 'ｉ': 'i', 'ｊ': 'j', 'ｋ': 'k', 'ｌ': 'l', 'ｍ': 'm', 'ｎ': 'n',
        'ｏ': 'o', 'ｐ': 'p', 'ｑ': 'q', 'ｒ': 'r', 'ｓ': 's', 'ｔ': 't', 'ｕ': 'u',
        'ｖ': 'v', 'ｗ': 'w', 'ｘ': 'x', 'ｙ': 'y', 'ｚ': 'z',
        '０': '0', '１': '1', '２': '2', '３': '3', '４': '4', '５': '5', '６': '6',
        '７': '7', '８': '8', '９': '9'
    }
    return ''.join(fullwidth_to_halfwidth_dict.get(char, char) for char in text)


def ensure_blank_line_before_titles(text):
    """
    【新增修复函数】确保每个章节标题前都有空行（即 \n\n）。
    - 使用负向后查 (?<!\n)\n 精确匹配“恰好只有一个换行符”的情况。
    - 如果已经是 \n\n 或文首标题，则不额外添加。
    - 幂等：多次调用结果不变。
    - 配合 add_newline_after_chapter() 的 __NEWLINE__ 机制，
      无论原文标题前是否有换行，都能稳定输出带空行分隔的标题。
    """
    if not text:
        return text

    # 标题模式（与 add_chapter_word_counts 保持一致，支持带字数标注后的标题）
    title_pattern = (
        r'(?<!\n)\n'
        r'((?:第[0123456789零一二三四五六七八九十百千\d]+[章卷集部]|'
        r'（[0123456789一二三四五六七八九十百千]+）)[^「『《（\n\r]{0,80})'
    )
    # 把“单 \n + 标题”替换为 “\n\n + 标题”
    return re.sub(title_pattern, r'\n\n\1', text)


def format_text(text, add_chapter_wordcount=True, line_length=None):
    """
    核心格式化函数。按固定流程处理文本：
    1. 早期清理（总字数行 + 旧标注）→ 保证字数统计纯净
    2. 分隔符识别与标记
    3. 标点/符号/数字规范化 + 段落初步处理
    4. 标题换行标记（__NEWLINE__）
    5. 段落切分与格式化
    6. 总字数统计（此时已无辅助标注影响）
    7. 标题分段 + 添加章节字数（幂等）
    8. 新增：ensure_blank_line_before_titles() → 稳定空行
    9. -l 智能换行 或 默认全角缩进
    10. 配对标点检查（仅警告，不改内容）
    """
    # ========== 步骤 0: 早期清理（关键修复点） ==========
    # 删除已有的总字数统计行（如果存在）
    if text.startswith("总字数："):
        lines = text.split('\n', 1)
        text = lines[1].lstrip() if len(lines) > 1 else ""

    # 【核心修复1】尽早移除所有章节字数辅助标注
    # 这样后续的 total_words 计算、标题匹配、段落处理等都不会受到污染
    text = re.sub(r'（本章字数：\d+）', '', text)

    # ========== 步骤 1: 找到最后一个 ■ 分隔正文与可能存在的后记 ==========
    last_square_index = text.rfind('■')
    if last_square_index != -1:
        preamble_content = text[:last_square_index]
        end_content = text[last_square_index + 1:]
    else:
        preamble_content = text
        end_content = ""

    # ========== 步骤 2: 分隔符识别（*** *** 之类的星号行 → 特殊标记） ==========
    divider = "＊＊＊　＊＊＊　＊＊＊　＊＊＊　＊＊＊\n"
    divider_marker = "【分隔符】"
    divider_pattern = re.compile(r'[\s\*　※＊]*[\*※＊][\s\*　※＊]*', re.MULTILINE)

    processed_lines = []
    for line in preamble_content.split('\n'):
        if divider_pattern.match(line.strip()) or line.strip() == '…':
            processed_lines.append(divider_marker)
        else:
            processed_lines.append(line)
    preamble_content = '\n'.join(processed_lines)

    # ========== 步骤 3: 标点符号规范化 + 初步处理 ==========
    punctuation_map = {
        ',': '，', '.': '。', '!': '！', '?': '？',
        ';': '；', ':': '：', '(': '（', ')': '）',
        '<': '《', '>': '》', '"': '「', "'": '‘',
        '“': '「', '”': '」', '~': '～', '*': '＊', "．": "."
    }
    punctuation_pattern = re.compile(r'([,\.! ?;:()<>"“”\'*~])')

    preamble_content = re.sub(r'<p>', '\n\n', preamble_content.strip())
    preamble_content = add_newline_after_chapter(preamble_content)  # 插入标题标记
    preamble_content = re.sub(r'\n{3,}', '\n\n', preamble_content.strip())
    preamble_content = re.sub(r'—+', '——', preamble_content.strip())

    # 按“句子结束标点 + 换行”切分逻辑段落
    paragraphs = re.split(
        r'(?<=[。？；！＊…”」』～》）—…])[\n\r]{1,}',
        preamble_content
    )

    formatted_paragraphs = []
    for para in paragraphs:
        para = re.sub(r'\n+', ' ', para.strip())
        para = para.strip()
        # 标点映射
        para = punctuation_pattern.sub(
            lambda m: punctuation_map.get(m.group(1), m.group(1)), para
        )
        # 连续标点规范
        para = re.sub(r'[\.．·。…]{2,}', '…', para)
        para = re.sub(r'…{1,}', '……', para)
        para = re.sub(r'・{2,}', '……', para)
        para = re.sub(r'！{2,}', '！', para)
        para = re.sub(r'？{2,}', '？', para)
        para = re.sub(r'[~～]+', '～', para)
        para = re.sub(r'-{2,}', '——', para)
        para = re.sub(r'—{1,}', '——', para)
        para = re.sub(r'─{1,}', '——', para)
        # 全角数字转半角
        para = para.translate(str.maketrans('１２３４５６７８９０', '1234567890'))
        # 智能换行标记
        para = re.sub(r'(?<=[。！？…]) +', '\n', para)
        para = fullwidth_to_halfwidth(para)
        para = replace_whitespace_in_brackets(para)
        para = replace_spaces_except_after_letters(para)
        para = re.sub(r'\n{2,}', '\n', para)
        formatted_paragraphs.append(para)

    formatted_preamble_content = '\n'.join(formatted_paragraphs)
    formatted_preamble_content = formatted_preamble_content.lstrip('\n')
    formatted_preamble_content = remove_newlines_in_brackets(formatted_preamble_content)
    formatted_preamble_content = re.sub('__NEWLINE__', '\n', formatted_preamble_content)

    # ========== 步骤 4: 统计总字数（此时已无任何辅助标注影响，排除排版用的全角空格 '　' 等） ==========
    total_words = len(re.sub(WORD_COUNT_WHITESPACE, '', formatted_preamble_content))

    # 恢复分隔符
    formatted_preamble_content = formatted_preamble_content.replace(divider_marker, divider)

    # ========== 步骤 5: 添加章节字数统计（幂等） ==========
    formatted_preamble_content = add_chapter_word_counts(formatted_preamble_content)
    if not add_chapter_wordcount:
        formatted_preamble_content = re.sub(r'（本章字数：\d+）', '', formatted_preamble_content)

    # ========== 步骤 6: 【核心修复2】确保标题前空行（稳定输出） ==========
    formatted_preamble_content = ensure_blank_line_before_titles(formatted_preamble_content)

    # ========== 步骤 7: 行格式化（-l 模式 或 默认缩进） ==========
    if line_length and isinstance(line_length, int) and line_length > 0:
        logical_blocks = formatted_preamble_content.strip().split('\n')

        # 合并孤立的禁用标点行（避免单独的 。 ！ 等难看）
        cleaned_blocks = []
        for block in logical_blocks:
            stripped = block.strip()
            if stripped in FORBIDDEN_START_PUNCTS:
                if cleaned_blocks:
                    cleaned_blocks[-1] = cleaned_blocks[-1] + stripped
                continue
            cleaned_blocks.append(block)

        final_lines = []
        for block in cleaned_blocks:
            if not block.strip():
                final_lines.append('')  # 保留空行（标题分隔用）
                continue
            if is_chapter_title(block):
                centered = center_title(block.strip(), line_length)
                final_lines.append(centered)
            else:
                wrapped = wrap_body_paragraph(block, line_length)
                final_lines.extend(wrapped)
        formatted_preamble_content = '\n'.join(final_lines)
    else:
        # 默认模式：每行添加全角缩进
        formatted_preamble_content = '　　' + re.sub(
            r'\n', '\n　　', formatted_preamble_content.strip()
        )
        # 清理仅含缩进的空行
        formatted_preamble_content = '\n'.join(
            '' if not line.strip() else line
            for line in formatted_preamble_content.split('\n')
        )

    # ========== 步骤 8: 配对标点检查（使用原始输入，仅打印警告） ==========
    punctuation_check = check_paired_punctuation(text)
    if punctuation_check:
        print("-" * 50)
        print("标点符号配对检查结果:")
        print(punctuation_check)
        print("-" * 50)

    # ========== 最终组装 ==========
    final_text = f"总字数：{total_words}\n\n{formatted_preamble_content}"
    if last_square_index != -1:
        final_text += '■' + end_content

    return final_text


def process_file(input_path, output_path, add_chapter_wordcount=True, line_length=None):
    """
    读取 input_path，调用 format_text 处理，写出到 output_path。
    强制使用 UTF-8 + Unix 换行符。
    """
    with open(input_path, 'r', encoding='utf-8') as f:
        text = f.read()

    formatted_text = format_text(
        text,
        add_chapter_wordcount=add_chapter_wordcount,
        line_length=line_length
    )

    with open(output_path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(formatted_text)


if __name__ == '__main__':
    import sys

    # ========== 命令行参数解析（支持 -l N 和 --no-wordcount/-n 任意顺序） ==========
    add_chapter_wordcount = True
    line_length = None

    if '--no-wordcount' in sys.argv or '-n' in sys.argv:
        add_chapter_wordcount = False

    if '-l' in sys.argv:
        try:
            l_idx = sys.argv.index('-l')
            if l_idx + 1 < len(sys.argv):
                line_length = int(sys.argv[l_idx + 1])
                if line_length <= 0:
                    raise ValueError
            else:
                raise ValueError
        except Exception:
            print("Error: -l 需要一个正整数参数，例如：python pb.py in.txt -l 40")
            sys.exit(1)

    # 过滤出位置参数（排除标志及其值）
    positional = []
    skip_next = False
    for arg in sys.argv[1:]:
        if skip_next:
            skip_next = False
            continue
        if arg in ('--no-wordcount', '-n', '-l'):
            if arg == '-l':
                skip_next = True
            continue
        positional.append(arg)

    if len(positional) < 1:
        print("用法: python pb.py input.txt [output.txt] [-l N] [--no-wordcount | -n]")
        print("  -l N               启用智能换行模式，每行最多 N 个字符（推荐 35~50）")
        print("  --no-wordcount / -n  不添加章节字数统计（默认会添加）")
        print("\n详细说明请查看文件顶部的文档字符串。")
        sys.exit(1)

    input_path = positional[0]

    if len(positional) == 1:
        base_name, ext = os.path.splitext(input_path)
        output_path = f"{base_name}={ext}"
    else:
        output_path = positional[1]

    process_file(
        input_path,
        output_path,
        add_chapter_wordcount=add_chapter_wordcount,
        line_length=line_length
    )
    print(f"格式化完成，输出文件已保存为：{output_path}")
