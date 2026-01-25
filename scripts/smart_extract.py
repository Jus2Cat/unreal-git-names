import sys
import os
import struct

def extract_actor_label(file_path):
    try:
        with open(file_path, "rb") as f:
            data = f.read()
    except FileNotFoundError:
        return None

    label_bytes = b"ActorLabel\x00"
    
    # Находим ВСЕ вхождения
    offsets = []
    idx = data.find(label_bytes)
    while idx != -1:
        offsets.append(idx)
        idx = data.find(label_bytes, idx + 1)

    if not offsets:
        return None

    # Гипотеза 8: Используем только ПОСЛЕДНЕЕ вхождение (секция ExportData)
    last_index = offsets[-1]
    
    search_start = last_index + len(label_bytes)
    search_limit = search_start + 120 
    
    current_pos = search_start
    found_value = None
    
    while current_pos < search_limit and current_pos < len(data) - 4:
        try:
            str_len = struct.unpack('<i', data[current_pos:current_pos+4])[0]
        except:
            break
            
        if 1 < str_len < 128:
            # Проверяем дистанцию (в данных объекта обычно есть заголовок свойства)
            distance_from_label = current_pos - search_start
            if distance_from_label < 4: # Сократим до 4 для надежности в последней секции
                current_pos += 1
                continue

            str_start = current_pos + 4
            str_end = str_start + str_len
            if str_end < len(data):
                potential_str_bytes = data[str_start:str_end-1]
                
                if all(32 <= b < 127 or b == 95 for b in potential_str_bytes):
                     decoded = potential_str_bytes.decode('ascii')
                     if decoded not in ["StrProperty", "NameProperty", "ObjectProperty", "None"]:
                        found_value = decoded
                        break
        
        # Unicode check
        if -128 < str_len < -1:
             utf_len = -str_len
             str_start = current_pos + 4
             str_end = str_start + (utf_len * 2)
             if str_end < len(data):
                 potential_str_bytes = data[str_start:str_end-2]
                 try:
                     decoded = potential_str_bytes.decode('utf-16le')
                     if decoded not in ["StrProperty", "NameProperty", "ObjectProperty", "None"]:
                        found_value = decoded
                        break
                 except:
                     pass

        current_pos += 1

    return [found_value] if found_value else []

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python smart_extract.py <uasset_path>")
        sys.exit(1)
        
    fpath = sys.argv[1]
    print(f"Analyzing {os.path.basename(fpath)} (Last Occurrence Strategy)...")
    results = extract_actor_label(fpath)
    
    if results:
        print("Found Actor Label:")
        for r in results:
            print(f"- {r}")
    else:
        print("No label found.")