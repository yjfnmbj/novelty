#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
author:lxy
date:2025-08-30
update:2026-06-067
================================================================================
pb.py - 中文文本格式化处理脚本（专为小说、文档排版优化）
================================================================================

【功能概述】
对中文文本进行专业排版处理：
- 标点符号规范化（半角转全角、连续标点合并、破折号/省略号规范等）
- 英文/数字全角转半角
- 智能段落分割与换行（支持 -l 模式进行优雅换行 + 标题居中 + 首行缩进）
- 自动识别「第X章」「第X卷」「（1）」「（一）」等章节/小节标题
- 在标题后追加「（本章字数：XXXX）」统计（可关闭）
- 统计全文总字数（不含辅助标注）
- 检测配对标点符号（「」『』《》【】（）等）是否成对，报告异常位置
- 特殊处理引号内换行、空格、英文后空格保留等
- 支持分隔符（*** ***）识别与美化

【核心 Bug 修复（本次更新重点）】
1. **字数统计受辅助内容污染 Bug**：
   - 问题：如果输入已包含「（本章字数：3150）」等旧标注，统计总字数和章节字数时会把这些辅助字符算进去，导致字数偏大，且反复处理后字数变化不稳定。
   - 修复： 在 format_text() 最开始（处理总字数行之后）立即全局移除所有「（本章字数：\\d+）」标注。
     这样后续所有格式化、标题匹配、段落处理、total_words 计算、章节字数计算都在“干净正文”上进行。
     add_chapter_word_counts() 内部仍保留移除逻辑以保持函数幂等性和独立可调用性。
   - 效果：总字数与各章字数完全不受辅助标注影响，幂等性完美（反复运行结果一致）。

2. **章节标题前空行被吃掉 + 输出不稳定 Bug**：
   - 问题：当原文中章节标题前没有换行符（紧跟上一句末尾标点），或处理过程中空行被合并，第一次输出时标题前只有单换行（或被并入正文段落），必须把输出再跑一次脚本才“正确”（标题前出现空行）。
   - 根本原因分析：
     a. add_newline_after_chapter() 用 __NEWLINE__ 占位符包裹标题，意图在 split 后制造分离。
     b. 但 re.split(r'(?<=[。？；！...])[\n\r]{1,}', ...) 仅在“句子结束标点 + 换行”处切分段落。
        如果标题前 originally 无 \n，则 split 不会触发，标题被塞进前一个段落块内，__NEWLINE__ 只提供单 \n。
     c. -l 模式下 logical_blocks 处理会跳过空块，导致即使有 \n\n 也无法在最终输出体现空行。
     d. 多次运行后状态变化（第一次产生 \n，第二次 split 行为改变），造成不稳定。
   - 修复方案（双管齐下，彻底稳定）：
     1. 在 add_newline_after_chapter() 保持原有 marker 机制（最小改动）。
     2. 新增 ensure_blank_line_before_titles() 函数，在 add_chapter_word_counts() 之后、
        行格式化之前，对最终文本做一次正则替换：把“单个 \n + 标题”升级为 “\n\n + 标题”。
        使用负向后查 (?<!\n)\n 精确匹配“恰好单换行”的情况，幂等且不影响已有空行或文首标题。
     3. 修改 -l 模式下的 block 处理逻辑：遇到空块时 append('') 而不是 continue 跳过，
        配合 wrap_body_paragraph('') 返回 [] 的特性，在 join 时自然产生空行分隔。
        （正文段落间仍保持单换行 + 首行缩进的原有风格，只有标题周围才有空行）
   - 效果：无论原文标题前是否有换行、是否有旧标注，第一次运行即可输出“标题前始终带空行”的稳定结果。
     再跑任意次数结果完全一致（幂等）。

【使用方法】
python pb.py <input.txt> [output.txt] [-l N] [--no-wordcount | -n]

参数说明：
  input.txt          必选，待处理的 UTF-8 文本文件（可含全半角混杂、旧格式等）
  output.txt         可选，输出文件名。默认在 input 同目录生成 input=.txt（注意等号）
  -l N               可选，启用智能换行模式，N 为每行最大字符数（推荐 35~50）。
                     效果：
                       - 章节标题自动居中（使用全角空格 '　' 填充）
                       - 正文段落：首行 '　　' 缩进，续行无缩进
                       - 句尾标点（。！？等）换行时智能处理，避免孤立标点开头
                       - 双标点（…… ——）可单独成短行
                       - 标题与正文间自动空行分隔
  --no-wordcount, -n 可选，关闭“在标题后追加（本章字数：XXXX）”，仅做格式化

示例：
  python pb.py novel.txt                    # 默认处理，生成 novel=.txt，带字数统计 + 空行标题
  python pb.py novel.txt formatted.txt -l 40   # 智能换行40字/行，带字数
  python pb.py novel.txt -n                 # 不加字数统计
  python pb.py novel.txt out.txt -l 45 -n   # 智能换行 + 无字数统计

【注意事项】
- 输入输出均为 UTF-8，强制使用 Unix 换行符（\n）
- 脚本具有高度幂等性，建议处理后直接使用输出，无需担心重复运行损坏
- 配对标点检查结果会打印到控制台（警告类），不影响输出文件
- 如需自定义更多规则，可修改 FORBIDDEN_START_PUNCTS、DOUBLE_PUNCTS 等常量
- 本脚本为纯文本处理，不依赖任何外部库（标准库 re + os + sys）

版本：2026-06 修复增强版（详细注释版）
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
FORBIDDEN_START_PUNCTS = {'。', '？', '！', '，', '；', '：', '、'}  # 禁止单独成行的标点
DOUBLE_PUNCTS = {'……', '——', '———', '…'}  # 可单独成短行的双标点


def wrap_body_paragraph(para_text, width):
    """
    将正文段落智能换行到 <= width 字符。
    - 仅第一行添加首行缩进 '　　'
    - 续行无缩进
    - 句尾标点换行时：若下一行会以单个 FORBIDDEN_START_PUNCTS 开头，则“拉回”当前行（允许超宽1字符）
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
        # 统计字数：去除所有空白字符（\s 包括空格、\n、\t、全角空格等）
        word_count = len(re.sub(r'\s+', '', chapter_content))
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

    # ========== 步骤 4: 统计总字数（此时已无任何辅助标注影响） ==========
    total_words = len(re.sub(r'\s+', '', formatted_preamble_content))

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
