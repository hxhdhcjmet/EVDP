# 抖音评论写入
import aiofiles
import json
import datetime
import os
from core.paths import DATA_DIR


class CommentWriter:

    def __init__(self, filename: str):
        # 在data文件夹下创建文件
        if not filename:
            filename = self._default_name_()

        data_dir = str(DATA_DIR)

        # 创建data文件夹
        os.makedirs(data_dir,exist_ok=True)
        file_dir = os.path.join(data_dir,filename)

        # 创建对应文件夹
        os.makedirs(file_dir,exist_ok=True)
        filepath = os.path.join(file_dir,f"{filename}.jsonl")

        self.filepath = filepath
        self.file = None
        print(f"文件保存至:{self.filepath}")
    
    @staticmethod
    def _default_name_():
        # 默认时间为文件名
        current_time = datetime.datetime.now()
        time_str = current_time.strftime(r'%Y%m%d%H%M%S')
        return time_str


    async def open(self):
        self.file = await aiofiles.open(
            self.filepath,
            mode="w",
            encoding="utf-8"
        )

    async def write(self, comment: dict):

        line = json.dumps(comment, ensure_ascii=False) + "\n"
        await self.file.write(line)

    async def close(self):

        if self.file:
            await self.file.flush()
            await self.file.close()
