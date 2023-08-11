import typing
import PyPDF2
from PyPDF2.generic import IndirectObject


def get_bookmarks(reader: PyPDF2.PdfReader, strip: bool = False):
    """
    从PDF文件中读取书签内容
    :param reader:
    :param strip: 是否处理去除标题两端的空白字符
    :return: 书签列表，包含了书签层级关系，列表元素是一个字典，该字典格式如下：
        {
            'title': str,
            'page_number': int,
            'children': list
        }
    """
    bookmarks = []
    for item in reader.outline:
        title = item.title
        if strip:
            title = title.strip()
        bookmarks.append({
            'title': title,
            'page_number': find_page_number(reader, item.page),
            'children': None
        })
    ret = process_bookmarks_level(bookmarks)
    print('Bookmarks count: {}'.format(ret[0]))
    return ret[1]


def process_bookmarks_level(bookmarks: list, level: int = 1, last_level_index: int = -1):
    """
    处理书签的层级关系。函数将会返回一个元组，该元组有两个元素
    第一个是层级level包含的所有子书签个数（不仅仅只是下一级书签），第二个是包含level下的下一级子书签的列表
    :param level:
    :param bookmarks:
    :param last_level_index: 上一层级标签在list中的位置
    :return: 返回已经处理好书签层级的列表
    """
    cur_level_bms = []
    index = last_level_index + 1
    counter = 0
    while index < len(bookmarks):
        item = bookmarks[index]
        bm_level = get_level_by_title(item['title'])
        if bm_level == level:  # 当前层级的书签
            cur_level_bms.append(bookmarks[index])
            counter += 1
        elif bm_level > level:  # 更深层级的书签
            ret = process_bookmarks_level(bookmarks, level + 1, index - 1)
            cur_level_bms[len(cur_level_bms) - 1]['children'] = ret[1]
            counter += ret[0]
            index += ret[0] - 1  # 跳过深层级子书签
        else:  # 更浅层级的书签
            break
        index += 1
    return counter, cur_level_bms


def get_level_by_title(title):
    """
    根据给定的书签标题title判断书签的层级数，该函数采取的是由"."的个数决定层级数的策略。
    :param title:
    :return:
    """
    count = count_dots_between(title)
    return count + 1


def count_dots_between(text):
    # 移除开头的空白字符
    text = text.lstrip()
    # 找到第一个空白字符的索引
    space_index = text.find(' ')
    if space_index == -1:
        # 如果没有找到空白字符，说明整个字符串都是非空白字符
        return text.count('.')
    else:
        # 计算从首个非空白字符到空白字符之间的 . 的个数
        return text[:space_index].count('.')


def add_bookmarks(writer: PyPDF2.PdfWriter, bookmarks: list, parent=None):
    """
    将经过层级处理的书签添加到PDF当中，本函数采用了递归调用来实现添加多层级书签
    :param writer:
    :param bookmarks:
    :param parent: list中的所有的书签都将作为parent的子标签
    :return:
    """
    for item in bookmarks:
        ret = writer.add_outline_item(
            title=item['title'],
            # bm.get_bookmarks(reader)返回的页码是第i页，这里需要的是从0开始的序列号
            page_number=item['page_number'] - 1,
            parent=parent
        )
        if item['children'] is not None:
            add_bookmarks(writer, item['children'], ret)


def extract_bookmarks(pdf_file: str, out_file: str):
    """
    提取PDF文件中的标签，并导出至指定文件
    :param pdf_file: 带读取书签PDF文件的路径
    :param out_file: 读取书签信息以后，将书签输出到该文件当中
    """
    with open(pdf_file, 'rb') as in_stream:
        reader = PyPDF2.PdfReader(in_stream)
        bms = get_bookmarks(reader, True)
    with open(out_file, 'wt') as out_stream:
        write_bookmarks(bms, out_stream)


def write_bookmarks(bookmarks: list, out_stream, level: int = 1):
    indent_count = level - 1                # 缩进格数
    for item in bookmarks:
        out_stream.write('#{:<4} '.format(item['page_number']))
        for i in range(indent_count):
            out_stream.write('\t')
        out_stream.write(item['title'] + '\n')
        if item['children'] is not None:    # 处理子书签
            write_bookmarks(item['children'], out_stream, level + 1)


def find_page_number(pdf_reader: PyPDF2.PdfReader, target: typing.Union[IndirectObject, int]):
    """
    根据给定的target查询该对象在整个PDF文件中表示的页码
    :param pdf_reader:
    :param target:
    :return:
    """
    if isinstance(target, int):
        return target
    else:
        for index, page in enumerate(pdf_reader.pages):
            ref = page['/Contents'].indirect_reference
            # ref.idnum表示的是当前页面末尾，随着遍历的进行，ref.idnum在增加
            if ref.idnum >= target.idnum:
                return index + 1
    return -1


def get_bookmarks_from_txt(txt_file: str):
    """
    按照一定的格式从txt文本文件中读取书签，txt文件内的标签需要符合以下格式：
    每一行前个字符：需要是#1234格式，数字最大为4位数，少位用空格补
    之后再留一个空格，接下来就是标题：#1234 标题
    每深入一级子标签，在标题和页码之间（即第7个字符开始），添加一个'\t'字符，
    '\t'字符个数加一即当前书签的层级
    :return: 书签列表，包含了书签层级关系
    """
    with open(txt_file, 'rt') as in_stream:
        bookmarks = read_bookmarks(in_stream)
    return bookmarks


def read_bookmarks(in_stream, level: int = 1):
    bms = []
    mark = in_stream.tell()
    line = in_stream.readline()
    while line and line.strip() != '':
        line_level = get_level_by_line(line)
        if line_level == level:
            slices = line.split(maxsplit=1)
            bms.append({
                'title': slices[1].strip(),
                'page_number': int(slices[0][1:]),
                'children': None
            })
        elif line_level > level:
            in_stream.seek(mark)
            bms[len(bms) - 1]['children'] = read_bookmarks(in_stream, level + 1)
        else:
            in_stream.seek(mark)
            break
        mark = in_stream.tell()
        line = in_stream.readline()
    return bms


def get_level_by_line(line: str):
    tabs_count = 0
    for i, char in enumerate(line[6:], start=6):    # 从第7个字符开始迭代
        if char == '\t':
            tabs_count += 1
        else:
            break                                   # 遇到第一个非'\t'字符，退出循环
    return tabs_count + 1


if __name__ == '__main__':
    # Test1
    # extract_bookmarks(
    #     'file/C++ Primer Plus .pdf',
    #     'file/bookmark_output.txt'
    # )

    # Test2
    # bookmarks = get_bookmarks(
    #     PyPDF2.PdfReader('file/C++ Primer Plus .pdf'),
    #     strip=True
    # )
    # for item in bookmarks:
    #     print(item)

    # Test3
    bms = get_bookmarks_from_txt('file/bookmark_output.txt')
    for item in bms:
        print(item)
