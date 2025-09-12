import asyncio
from pathlib import Path
import time
import os
from aiogram import Bot, Dispatcher

from app.config import settings
from app.handlers import router


def clean_downloads(folder: str = "downloads", days: int = 30):
    now = time.time()
    cutoff = now - days * 24 * 60 * 60

    folder_path = Path(folder)
    if not folder_path.exists():
        return []

    deleted_files = []

    for file in folder_path.iterdir():
        if file.is_file():
            mtime = file.stat().st_mtime
            if mtime < cutoff:
                try:
                    file.unlink()
                    deleted_files.append(file.name)
                except Exception as e:
                    print(f"Не удалось удалить {file}: {e}")

    return deleted_files


async def cleaner_task():
    while True:
        removed = clean_downloads("downloads", days=30)
        if removed:
            print("🗑 Удалены старые файлы:", removed)
        await asyncio.sleep(24 * 60 * 60)

async def main():
    bot = Bot(token=settings.bot_token)
    dp = Dispatcher()
    dp.include_router(router)

    print("✅ Бот запущен")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
