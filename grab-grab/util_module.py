import json

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
        with open(self.output_file, 'a', encoding='utf-8') as f:
             f.write(json.dumps(self.result, ensure_ascii=False)+'\n')
