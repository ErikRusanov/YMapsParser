import json
import os

class JSONWorker(object):
    """ Класс для работы с JSON файлом"""

    def __init__(self, flag, result, output_file):
        self.result = result
        self.output_file = output_file
        _selector = {
            "get": self.get_jsonwork,
            "set": self.set_jsonwork,
        }
        _selector[flag]()

    def get_jsonwork(self):
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(self.result, f, ensure_ascii=False, indent=4)

    def set_jsonwork(self):
        # Проверяем, существует ли файл и не пустой ли он
        if os.path.exists(self.output_file) and os.path.getsize(self.output_file) > 0:
            # Читаем существующий массив
            with open(self.output_file, 'r', encoding='utf-8') as f:
                try:
                    existing_data = json.load(f)
                    if not isinstance(existing_data, list):
                        existing_data = [existing_data]
                except json.JSONDecodeError:
                    # Если файл поврежден, начинаем с пустого массива
                    existing_data = []
        else:
            # Создаем новый файл с пустым массивом
            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump([], f, ensure_ascii=False)
            existing_data = []
        
        # Добавляем новый объект в массив
        existing_data.append(self.result)
        
        # Записываем обновленный массив обратно в файл
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=4)
