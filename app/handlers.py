from aiogram import Router, F 
from aiogram.types import Message 
from aiogram.fsm.context import FSMContext 
from aiogram.fsm.state import StatesGroup, State 
import os 
from app.keyboards import main_kb 
from app.services import upload_to_drive, insert_image_into_sheet 

router = Router() 

class UploadStates(StatesGroup): 
    waiting_for_photo = State() 
    waiting_for_cell = State() 
    
@router.message(F.text == "/start") 
async def start(message: Message): 
    await message.answer("Привет! Я бот для вставки картинок в Google Sheets.", reply_markup=main_kb) 

@router.message(F.text == "📤 Загрузить фото") 
async def ask_photo(message: Message, state: FSMContext): 
    await message.answer("Отправь фото для загрузки 📸") 
    await state.set_state(UploadStates.waiting_for_photo) 

@router.message(UploadStates.waiting_for_photo, F.photo) 
async def get_photo(message: Message, state: FSMContext): 
    photo = message.photo[-1] 
    file = await message.bot.get_file(photo.file_id) 
    file_path = f"downloads/{photo.file_id}.jpg" 
    os.makedirs("downloads", exist_ok=True) 
    await message.bot.download_file(file.file_path, file_path) 
    await state.update_data(file_path=file_path) 
    await message.answer("✅ Фото сохранено!\nТеперь введи ячейку (например: A1):") 
    await state.set_state(UploadStates.waiting_for_cell) 
    
@router.message(UploadStates.waiting_for_cell)
async def get_cell(message: Message, state: FSMContext):
    data = await state.get_data()
    file_path = data["file_path"]

    default_column = "J"
    row_number = message.text.strip()
    
    if not row_number.isdigit():
        await message.answer("❌ Пожалуйста, введи только номер строки (число).")
        return

    cell = f"{default_column}{row_number}"

    image_url = upload_to_drive(file_path, os.path.basename(file_path))
    insert_image_into_sheet(cell, image_url)

    await message.answer(f"✅ Картинка вставлена в {cell}", reply_markup=main_kb)
    await state.clear()