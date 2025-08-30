author:lxy
date:2025-08-30

import re
import os


def check_paired_punctuation(text):
    """
    检测配对标点符号的数量是否一致，并找出不配对的具体位置
    :param text: 输入的文本
    :return: 检测结果信息
    """
    # 定义需要检查的配对标点
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
            results.append(f"警告: {pair_name} 数量不匹配 - 左{left}: {left_count}个, 右{right}: {right_count}个")
            
            # 找出不配对的具体位置
            if left_count > right_count:
                # 找出多余的左标点
                find_extra_punctuations(text, left, right, pair_name, '左', detailed_warnings)
            else:
                # 找出多余的右标点
                find_extra_punctuations(text, right, left, pair_name, '右', detailed_warnings)
        else:
                pass
            #results.append(f"正常: {pair_name} 数量匹配 - 各{left_count}个")
    
    # 检查嵌套是否正确（比如「」内部是否有多余的「）
    check_nesting(text, detailed_warnings)
    
    # 合并结果
    all_results = results + detailed_warnings
    return "\n".join(all_results)

def find_extra_punctuations(text, main_char, paired_char, pair_name, side, warnings):
    """
    找出多余的标点符号及其上下文
    """
    positions = []
    for i, char in enumerate(text):
        if char == main_char:
            positions.append(i)
    
    for pos in positions:
        # 检查这个标点是否真的多余（前后没有配对标点）
        if not has_proper_pair(text, pos, main_char, paired_char, side):
            # 获取上下文
            start = max(0, pos - 10)
            end = min(len(text), pos + 11)
            context = text[start:end]
            
            # 标记问题位置
            if start < pos:
                marked_context = context[:pos-start] + '【' + context[pos-start] + '】' + context[pos-start+1:]
            else:
                marked_context = '【' + context[0] + '】' + context[1:]
            
            warnings.append(f"  位置: 第{count_lines(text, pos)}行附近 - '{marked_context}'")

def has_proper_pair(text, pos, main_char, paired_char, side):
    """
    检查标点是否有正确的配对
    """
    if side == '左':
        # 检查左标点后面是否有配对的右标点
        next_right = text.find(paired_char, pos + 1)
        if next_right != -1:
            # 检查中间是否还有其他左标点（嵌套）
            between_text = text[pos + 1:next_right]
            if main_char not in between_text:
                return True
    else:
        # 检查右标点前面是否有配对的左标点
        prev_left = text.rfind(paired_char, 0, pos)
        if prev_left != -1:
            # 检查中间是否还有其他右标点
            between_text = text[prev_left + 1:pos]
            if main_char not in between_text:
                return True
    return False

def check_nesting(text, warnings):
    """
    检查标点嵌套是否正确
    """
    # 检查「」嵌套
    check_specific_nesting(text, '「', '」', '「」', warnings)
    check_specific_nesting(text, '『', '』', '『』', warnings)
    check_specific_nesting(text, '《', '》', '《》', warnings)

def check_specific_nesting(text, left_char, right_char, pair_name, warnings):
    """
    检查特定标点对的嵌套情况
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
                marked_context = context[:i-start] + '【' + context[i-start] + '】' + context[i-start+1:]
                warnings.append(f"嵌套错误: {pair_name} 有多余的右标点 - 第{count_lines(text, i)}行: '{marked_context}'")
    
    # 检查栈中剩余的左标点（未闭合的）
    for pos in stack:
        start = max(0, pos - 10)
        end = min(len(text), pos + 11)
        context = text[start:end]
        marked_context = context[:pos-start] + '【' + context[pos-start] + '】' + context[pos-start+1:]
        warnings.append(f"嵌套错误: {pair_name} 有未闭合的左标点 - 第{count_lines(text, pos)}行: '{marked_context}'")

def count_lines(text, position):
    """
    计算某个位置在文本中的行号
    """
    return text[:position].count('\n') + 1

def add_newline_after_chapter(text):
    """
    在「第XX章」或「（一）」后面添加换行符，并移除换行符后的空格。
    :param text: 输入的文本
    :return: 处理后的文本
    """
    # 匹配「第XX章」或「（一）」的格式
    pattern = re.compile(r'(第[0123456789零一二三四五六七八九十百千\d]+[章卷集部]|（[0123456789一二三四五六七八九十百千]+）)')
    # 在章节后面添加换行符
    result = pattern.sub(r'\n\1\n', text)
    # 移除换行符后的空格
    result = re.sub(r'(第[0123456789零一二三四五六七八九十百千\d]+[章卷集部]\n|（[0123456789一二三四五六七八九十百千]+）\n)\s+', r'\1', result)
    return result

def replace_spaces_except_after_letters(text):
    """
    替换除英文字母后的所有空格，保留英文字母后的空格。
    :param text: 输入的文本
    :return: 处理后的文本
    """
    # 使用一个特殊标记替换英文字母后的空格
    marker = '__SPACE__'
    text = re.sub(r'(?<=[a-zA-Z]) ', marker, text)
    
    # 删除所有剩余的空格
    text = re.sub(r'[^\S\n]+', '', text)
    
    # 将特殊标记替换回空格
    text = text.replace(marker, ' ')
    
    return text

def remove_newlines_in_brackets(text):
    """
    删除「」或（）之间的换行符。但是，如果原文的「」的（）不配对，将导致错误的段落合并
    :param text: 输入的文本
    :return: 处理后的文本
    """
    # 匹配「」或（）之间的内容
    pattern = re.compile(r'(「(.{1,999}?)」|（(.{1,999}?)）)', re.DOTALL) # 最大匹配999个字符内的段落合并
    
    # 替换函数：去掉匹配内容中的换行符
    def replace_newlines(match):
        # 获取「」或（）之间的内容
        content = match.group(2) if match.group(2) is not None else match.group(3)
        if content is not None:  # 确保 content 不是 None
            content = content.replace('\n', '')  # 去掉换行符
            return f'「{content}」' if match.group(2) is not None else f'（{content}）'
        return match.group()  # 如果 content 是 None，返回原匹配内容
    
    result = pattern.sub(replace_newlines, text)
    return result

def replace_whitespace_in_brackets(text):
    """
    将」「之间的空白字符替换为一个换行符。
    
    :param text: 输入的文本
    :return: 处理后的文本
    """
    # 匹配」「之间的所有空白字符
    pattern = r'」\s*「'
    
    # 将匹配到的内容替换为」换行符「
    result = re.sub(pattern, '」\n「', text)
    
    return result

def fullwidth_to_halfwidth(text):
    """
    将全角的英文和数字字符转换为半角字符。
    
    :param text: 输入的文本，可能包含全角和半角字符的混合。
    :return: 处理后的文本，其中全角的英文和数字字符已被转换为半角。
    """
    # 定义一个字典，键为全角字符，值为对应的半角字符
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
        '７': '7', '８': '8', '９': '9','－':'-'
    }
    
    # 遍历输入文本的每个字符，并进行替换
    result = ''.join(fullwidth_to_halfwidth_dict.get(char, char) for char in text)
    
    return result

def format_text(text):
    """
    对文本进行格式化处理，包括标点符号规范化、特殊符号处理、数字规范化等。
    
    :param text: 输入的文本
    :return: 处理后的文本
    """

    # 定义分隔符样式
    divider = "＊＊＊　＊＊＊　＊＊＊　＊＊＊　＊＊＊\n"
    divider_marker = "【分隔符】"
    
    # 检查并删除已有的字数统计行
    if text.startswith("总字数："):
        lines = text.split('\n', 1)
        if len(lines) > 1:
            text = lines[1].lstrip()  # 删除字数统计行，并去除开头的空白
        else:
            text = ""

    # (1) 找到最后一个■的位置，进行分割
    last_square_index = text.rfind('■')
    
    if last_square_index != -1:
        preamble_content = text[:last_square_index]
        end_content = text[last_square_index + 1:]
    else:
        preamble_content = text
        end_content = ""
    
    # (2) 将一整行都是星号与空格的组合或单独成段的省略号替换为特殊标记
    processed_preamble_content = []
    divider_pattern = re.compile(r'^[\s\*　※＊]*[\*※＊][\s\*　※＊]*$', re.MULTILINE)
    
    # 预先替换分隔符行
    lines = preamble_content.split('\n')
    for line in lines:
        if divider_pattern.match(line.strip()) or line.strip() == '…':
            processed_preamble_content.append(divider_marker)
        else:
            processed_preamble_content.append(line)
    preamble_content = '\n'.join(processed_preamble_content)
    
    # (3) 对preamble_content进行排版
    # 标点符号规范化（半角转全角）
    punctuation_map = {
        ',': '，', '.': '。', '!': '！', '?': '？',
        ';': '；', ':': '：', '(': '（', ')': '）',
        '<': '《', '>': '》', '"': '「', "'": '‘',
        '“': '「', '”': '」', '~': '～','*':'＊' ,"．":"." 
    }
    punctuation_pattern = re.compile(r'([,\.! ?;:()<>"“”\'*~])')

    # 预processing text
    preamble_content = re.sub(r'<p>', '\n\n', preamble_content.strip())  # 将<p>替换为空行
    preamble_content = re.sub(r'\n{3,}', '\n\n', preamble_content.strip())  # 合并多余空行
    preamble_content = re.sub(r'—+', '——', preamble_content.strip())  # 处理一半的破折号

    paragraphs = re.split(r'(?<=[。？；！＊…”」』～》）])[\n\r]{1,}', preamble_content)  # 按段落分割

    formatted_paragraphs = []
    for para in paragraphs:
        # 合并被截断的段落，保留必要空格
        para = re.sub(r'\n+', ' ', para.strip())
        para = para.strip()
        # 标点符号规范化
        para = punctuation_pattern.sub(
            lambda m: punctuation_map.get(m.group(1), m.group(1)), para)

        # 特殊符号处理
        para = re.sub(r'[\.．·。…]{2,}', '…', para)  # 连续点号转省略号
        para = re.sub(r'…{2,}', '…', para)  # 规范多余省略号
        para = re.sub(r'[~～]+', '～', para)
        para = re.sub(r'-{2,}', '—', para)  # 连续短线转破折号

        # 数字规范化（全角转半角）
        para = para.translate(str.maketrans('１２３４５６７８９０', '1234567890'))

        # 智能分段：在句尾标点后换行
        para = re.sub(r'(?<=[。！？…]) +', '\n', para)

        para = fullwidth_to_halfwidth(para)
        para = replace_whitespace_in_brackets(para)
        para = replace_spaces_except_after_letters(para)

        # 移除多余换行
        para = re.sub(r'\n{2,}', '\n', para)

        formatted_paragraphs.append(""+para)

    # 使用Unix换行符，段落间保留一个空行
    formatted_preamble_content = '\n'.join(formatted_paragraphs)
    # 移除开头可能存在的换行符
    formatted_preamble_content = formatted_preamble_content.lstrip('\n')
    formatted_preamble_content = remove_newlines_in_brackets(formatted_preamble_content)
    # 在「第XX章」或「（一）」后面添加换行符
    formatted_preamble_content = add_newline_after_chapter(formatted_preamble_content)

    # (4) 统计字数
    total_words = len(re.sub(r'\s+', '', formatted_preamble_content))

    # (5) 最终合并，并替换分隔符
    formatted_preamble_content = formatted_preamble_content.replace(divider_marker, divider)

    # (6)正文全文首行缩进两个字符
    formatted_preamble_content = '　　'+re.sub(r'\n', '\n　　', formatted_preamble_content.strip()) 

    # (7)检测配对使用的标点是成对
    punctuation_check = check_paired_punctuation(text)
    if(punctuation_check):
        print("-" * 50)
        print("标点符号配对检查结果:")
        print(punctuation_check)
        print("-" * 50)

    final_text = f"总字数：{total_words}\n\n{formatted_preamble_content}"
    if last_square_index != -1:
        final_text += '■' + end_content

    return final_text

def process_file(input_path, output_path):
    """
    读取输入文件，格式化文本，并写入输出文件。
    :param input_path: 输入文件路径
    :param output_path: 输出文件路径
    """
    with open(input_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    formatted_text = format_text(text)
    
    # 强制使用Unix换行符
    with open(output_path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(formatted_text)

if __name__ == '__main__':
    import sys

    # 检查参数数量
    if len(sys.argv) < 2:
        print("Usage: python script.py input.txt [output.txt]")
        sys.exit(1)

    # 获取输入文件路径
    input_path = sys.argv[1]

    # 生成输出文件路径
    if len(sys.argv) == 2:
        # 如果只有一个参数，在原文件路径后加“=”作为新文件输出
        base_name, ext = os.path.splitext(input_path)
        output_path = f"{base_name}={ext}"
    else:
        # 如果有两个参数，使用第二个参数作为输出文件路径
        output_path = sys.argv[2]

    # 处理文件
    process_file(input_path, output_path)
    print(f"格式化完成，输出文件已保存为：{output_path}")
