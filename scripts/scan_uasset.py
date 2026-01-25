import sys
import os
import re

def extract_strings(filename, min_len=3):
    """
    Эвристический поиск строк в бинарном файле.
    Ищет последовательности ASCII и UTF-16 (Unicode), которые похожи на имена Unreal Engine.
    """
    with open(filename, "rb") as f:
        data = f.read()

    strings = []
    
    # 1. Поиск ASCII строк (обычные имена)
    # Ищем последовательности печатных символов
    ascii_pattern = re.compile(rb'[A-Za-z0-9_]{' + str(min_len).encode() + rb',}')
    for match in ascii_pattern.finditer(data):
        try:
            s = match.group().decode('ascii')
            strings.append(s)
        except:
            pass

    # 2. Поиск UTF-16 строк (имена Unreal часто хранятся как UTF-16LE)
    # Формат в UE: [Length < 0] [UTF-16 chars]
    # Но мы будем искать просто последовательности символов с нулями между ними
    # (T e x t) -> T\x00e\x00x\x00t\x00
    
    # Упрощенная эвристика для UTF-16 LE (English chars only for simplicity first)
    utf16_pattern = re.compile(rb'(?:[A-Za-z0-9_]\x00){' + str(min_len).encode() + rb',}')
    for match in utf16_pattern.finditer(data):
        try:
            # Декодируем байты
            s = match.group().decode('utf-16le')
            strings.append(s)
        except:
            pass

    return strings

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scan_uasset.py <path_to_uasset>")
        sys.exit(1)

    file_path = sys.argv[1]
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        sys.exit(1)

    print(f"--- Scanning: {os.path.basename(file_path)} ---")
    found_strings = extract_strings(file_path)
    
    print(f"Found {len(found_strings)} strings.")
    print("--- Top 20 Potential Actor Labels (Unique, Shortest First) ---")
    
    # Фильтрация мусора: убираем слишком длинные строки и совсем короткие
    filtered = [s for s in set(found_strings) if 3 < len(s) < 50]
    
    # Сортируем: сначала короткие (имена обычно короткие), потом по алфавиту
    filtered.sort(key=lambda x: (len(x), x))
    
    for s in filtered[:40]:
        print(s)
