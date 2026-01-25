import sys
import os

def find_context(file_path, search_term, context_bytes=64):
    try:
        with open(file_path, "rb") as f:
            data = f.read()
    except FileNotFoundError:
        print(f"Error: File {file_path} not found.")
        return

    term_bytes = search_term.encode('utf-8')
    # Также ищем в UTF-16LE, так как строки часто там
    term_bytes_utf16 = search_term.encode('utf-16le')

    matches = []

    # Helper to search and add matches
    def search_pattern(pattern, encoding_name):
        offset = 0
        while True:
            index = data.find(pattern, offset)
            if index == -1:
                break
            
            start = max(0, index - context_bytes)
            end = min(len(data), index + len(pattern) + context_bytes)
            
            matches.append({
                'offset': index,
                'type': encoding_name,
                'data_snippet': data[start:end]
            })
            offset = index + 1

    search_pattern(term_bytes, 'ASCII')
    search_pattern(term_bytes_utf16, 'UTF-16LE')

    print(f"--- Search Results for '{search_term}' in {os.path.basename(file_path)} ---")
    if not matches:
        print("Not found.")
        return

    for m in matches:
        print(f"\n[Match at Offset: {m['offset']} ({m['type']})]")
        snippet = m['data_snippet']
        
        # Hex view implementation
        hex_lines = []
        for i in range(0, len(snippet), 16):
            chunk = snippet[i:i+16]
            hex_str = ' '.join(f'{b:02x}' for b in chunk)
            text_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
            hex_lines.append(f"{hex_str:<48} | {text_str}")
        
        print('\n'.join(hex_lines))

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python analyze_structure.py <path_to_uasset> <search_term1> [search_term2...]")
        sys.exit(1)

    uasset_path = sys.argv[1]
    
    for term in sys.argv[2:]:
        find_context(uasset_path, term)
