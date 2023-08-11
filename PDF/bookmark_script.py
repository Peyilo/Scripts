import os

import PyPDF2
import bookmarks_process as bm
import glob


def process_pdf_bookmarks(pdf_path: str, out_path: str):
    """
    对没有分层级书签的PDF文件，完成书签的划分层级
    :param pdf_path:
    :param out_path:
    :return:
    """
    reader = PyPDF2.PdfReader(pdf_path)
    writer = PyPDF2.PdfWriter()
    # 新建PDF文件副本
    page_size = len(reader.pages)
    for page_number in range(page_size):
        page = reader.pages[page_number]
        writer.add_page(page)
    bm.add_bookmarks(
        writer=writer,
        bookmarks=bm.get_bookmarks(
            reader=reader,
            strip=True
        )
    )
    with open(out_path, 'wb') as output_file:
        writer.write(output_file)


if __name__ == '__main__':
    file_dir = 'E:\\电子书\\计算机\\待处理'
    # 获取指定文件夹下所有文件
    file_list = glob.glob(os.path.join(file_dir, '*.pdf'))
    for file in file_list:
        print('开始处理：{}'.format(file))
        slices = file.rsplit('.')
        process_pdf_bookmarks(file, '{}-副本.{}'.format(slices[0], slices[1]))

