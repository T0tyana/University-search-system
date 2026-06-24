import os

def parse_python_files(root_dir, output_file="project_code.txt"):
    with open(output_file, "w", encoding="utf-8") as out:
        for dirpath, dirnames, filenames in os.walk(root_dir):
            # Исключаем служебные папки
            if '__pycache__' in dirpath or '.venv' in dirpath or 'venv' in dirpath:
                continue
                
            for filename in filenames:
                if filename.endswith(".py"):
                    filepath = os.path.join(dirpath, filename)
                    relative_path = os.path.relpath(filepath, root_dir)
                    
                    out.write(f"\n{'='*50}\n")
                    out.write(f"FILE: {relative_path}\n")
                    out.write(f"{'='*50}\n\n")
                    
                    try:
                        with open(filepath, "r", encoding="utf-8") as f:
                            out.write(f.read())
                    except Exception as e:
                        out.write(f"Error reading file: {e}")

if __name__ == "__main__":
    # Запускаем парсинг начиная с текущей директории
    parse_python_files(".")
    print("Готово! Код собран в файл project_code.txt")