# 爬取信息写入文件功能
import json
import os
import aiofiles
from core.spider.zhihu.config import DATA_DIR

class Writer:
    def __init__(self, folder_name):
        self.folder = os.path.join(DATA_DIR, folder_name)
        os.makedirs(self.folder, exist_ok=True)
        self.filepath = os.path.join(self.folder, f"{folder_name}.jsonl")
    
    async def writer(self, queue):
        async with aiofiles.open(self.filepath, "a", encoding="utf-8") as f:
            while True:
                item = await queue.get()
                if item is None: break
                
                await f.write(json.dumps(item, ensure_ascii=False) + '\n')
                await f.flush()
                queue.task_done()

