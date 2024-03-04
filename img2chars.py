import typing as t
import os
import warnings

import cv2
from PIL import Image, ImageDraw, ImageFont

warnings.filterwarnings('ignore', category=DeprecationWarning)


class Color:
    """字符画颜色配置"""

    def __init__(
            self,
            background: t.Tuple[int, int, int] = (0, 0, 0),  # black
            text: t.Tuple[int, int, int] = (255, 255, 255),  # white
    ):
        self.background = background
        self.text = text


class Size:
    """生成图大小级别"""
    Medium = 1200
    Large = 2000

    resizes = {
        Medium: {
            'resize_width': 150,
            'resize_height_ratio': 1.85,
            'draw_length': 1200,
        },
        Large: {
            'resize_width': 250,
            'resize_height_ratio': 1.9,
            'draw_length': 2000,
        },
    }

    def __init__(self, size: int = Medium):
        self.resize_width = self.resizes[size]['resize_width']
        self.resize_height_ratio = self.resizes[size]['resize_height_ratio']
        self.draw_length = self.resizes[size]['draw_length']


class Convertor:
    """字符画转换器"""

    def __init__(
            self,
            original_image: t.Optional[cv2.typing.MatLike] = None,
            original_image_path: t.Optional[str] = None,
            output_image_path: t.Optional[str] = None,
            color: Color = Color(),
            size: Size = Size(Size.Medium),
            charset: t.Optional[t.List[str]] = None,
    ):
        """
        original_image 和 original_image_path 二选一, 优先使用 original_image

        :param original_image: 传入图片
        :param original_image_path: 传入图片路径
        :param output_image_path: 输出图片路径
        :param color: 字符画颜色配置, 默认为黑底白字
        :param size: 生成图大小级别
        :param charset: 绘图使用的字符集
        """
        self.original_image = original_image
        self.original_image_path = original_image_path
        self.output_image_path = output_image_path

        if not original_image and not original_image_path:
            raise ValueError('original_image 和 original_image_path 不能同时为空')

        if not output_image_path:
            raise ValueError('output_image_path 不能为空')

        if not original_image:
            if not os.path.exists(original_image_path):
                raise ValueError('图片不存在')
            self.original_image = cv2.imread(original_image_path)

        if not self.original_image.any():
            raise ValueError('图片加载失败')

        self.color = color
        self.size = size

        self.font_path = 'JetBrainsMono-Regular.ttf'
        self.font_size = 13
        self.font = ImageFont.truetype(self.font_path, self.font_size)

        self.charset = charset or list('MNHQ$OC?7>!:-;. ')

    def convert(self) -> str:
        """
        将图片转为字符画

        :return: 输出图片路径
        """
        text = self._img_to_chars()
        image = self._chars_to_img(text)
        image.save(self.output_image_path)
        return self.output_image_path

    def _gary_to_char(self, gray, alpha=256) -> str:
        """
        将灰度映射到字符上

        :param gray:
        :param alpha:
        :return:
        """
        if alpha == 0:
            return ' '
        unit = (alpha + 1) / len(self.charset)
        return self.charset[int(gray / unit)]

    def _img_to_chars(self) -> str:
        """
        将图片转为字符

        :return: 字符
        """
        # 转为灰度图
        gray = cv2.cvtColor(self.original_image, cv2.COLOR_BGR2GRAY)

        # 去噪声
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # 使用阈值分割
        _, thresh = cv2.threshold(blurred, 80, 255, cv2.THRESH_BINARY)

        # 重构图片大小
        width = self.size.resize_width
        height = int(thresh.shape[0] * width / thresh.shape[1])
        height = int(height / self.size.resize_height_ratio)
        resized = cv2.resize(thresh, (width, height))

        # 将图片转为字符
        text = ""
        for i in range(resized.shape[0]):
            for j in range(resized.shape[1]):
                text += self._gary_to_char(resized[i, j])
            text += '\n'

        return text

    def _chars_to_img(self, text: str) -> Image:
        """
        将字符转为图片

        :param text: 字符
        :return: 图片
        """
        # 初始化画布
        width = height = self.size.draw_length
        image = Image.new('RGB', (width, height), color=self.color.background)
        draw = ImageDraw.Draw(image)

        text_x = 10
        text_y = 10

        lines = text.split('\n')

        for line in lines:
            line_width, line_height = self.font.getsize(line)
            draw.text((text_x, text_y), line, font=self.font, fill=self.color.text)
            text_y += line_height

        return image
