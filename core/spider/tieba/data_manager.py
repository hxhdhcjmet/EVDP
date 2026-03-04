# 数据写入

import os
import json
import aiofiles
import aiohttp
try:
    from config import DATA_DIR
except ImportError:
    from core.spider.tieba.config import DATA_DIR

class DataManager:
    def __init__(self, folder_name: str):
        self.path = os.path.join(DATA_DIR, folder_name)
        self.img_path = os.path.join(self.path, "images")
        os.makedirs(self.img_path, exist_ok=True)
        self.file_path = os.path.join(self.path, "posts.jsonl")

    async def save_post_jsonl(self, data: dict):
        """异步追加写入"""
        async with aiofiles.open(self.file_path, mode='a', encoding='utf-8') as f:
            line = json.dumps(data, ensure_ascii=False, default=str)
            await f.write(line + '\n')
            # 配合 aiofiles，数据会由事件循环控制写入磁盘，不阻塞主线程

    async def download_image(self, session: aiohttp.ClientSession, url: str):
        name = url.split('/')[-1].split('?')[0]
        full_path = os.path.join(self.img_path, name if '.' in name else name + ".jpg")
        if os.path.exists(full_path): return
        try:
            async with session.get(url, timeout=10) as r:
                if r.status == 200:
                    async with aiofiles.open(full_path, mode='wb') as f:
                        await f.write(await r.read())
        except: pass