#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для очистки телефонных номеров в JSON файле с данными о турагентствах.
Удаляет номера, которые не являются корректными телефонами.
"""

import json
import re
import argparse
from typing import List, Dict, Any


def is_valid_phone(phone: str) -> bool:
    """
    Проверяет, является ли строка корректным телефонным номером.
    
    Корректные форматы:
    - +7 (xxx) xxx-xx-xx
    - +7 xxx xxx-xx-xx
    - 8 (xxx) xxx-xx-xx
    - 8 xxx xxx-xx-xx
    - +7xxxxxxxxxx
    - 8xxxxxxxxxx
    
    Args:
        phone: Строка с потенциальным телефонным номером
        
    Returns:
        True если номер корректный, False иначе
    """
    if not phone or not isinstance(phone, str):
        return False
    
    # Убираем все пробелы, скобки, дефисы для анализа
    clean_phone = re.sub(r'[\s\(\)\-]', '', phone)
    
    # Проверяем основные паттерны российских номеров
    patterns = [
        # +7 в начале, затем 10 цифр
        r'^\+7\d{10}$',
        # 8 в начале, затем 10 цифр  
        r'^8\d{10}$',
        # 7 в начале, затем 10 цифр (без +)
        r'^7\d{10}$'
    ]
    
    for pattern in patterns:
        if re.match(pattern, clean_phone):
            # Дополнительная проверка на длину оригинального номера
            # Слишком короткие номера (меньше 10 символов) отбрасываем
            if len(phone.strip()) >= 10:
                return True
    
    # Проверяем номера без кода страны, но с правильной длиной
    # Например: (495) 123-45-67 или 495 123-45-67
    if re.match(r'^\d{10}$', clean_phone) and len(phone.strip()) >= 10:
        return True
    
    # Короткие номера (меньше 7 цифр) точно не телефоны
    digit_count = len(re.sub(r'\D', '', phone))
    if digit_count < 7:
        return False
    
    return False


def clean_phones_in_data(data: List[Dict[str, Any]]) -> tuple[List[Dict[str, Any]], int, int]:
    """
    Очищает телефонные номера во всех записях.
    
    Args:
        data: Список словарей с данными о компаниях
        
    Returns:
        Tuple: (очищенные данные, количество удаленных номеров, количество обработанных компаний)
    """
    removed_count = 0
    processed_companies = 0
    
    for company in data:
        if 'phones' in company and isinstance(company['phones'], list):
            original_phones = company['phones'][:]
            valid_phones = []
            
            for phone in original_phones:
                if is_valid_phone(phone):
                    valid_phones.append(phone)
                else:
                    removed_count += 1
                    print(f"Удален номер: '{phone}' у компании '{company.get('name', 'Неизвестно')}'")
            
            company['phones'] = valid_phones
            processed_companies += 1
    
    return data, removed_count, processed_companies


def main():
    parser = argparse.ArgumentParser(description='Очистка телефонных номеров в JSON файле')
    parser.add_argument('input_file', help='Путь к входному JSON файлу')
    parser.add_argument('-o', '--output', help='Путь к выходному файлу (по умолчанию: перезаписывает входной)')
    parser.add_argument('--dry-run', action='store_true', help='Показать что будет удалено, но не сохранять изменения')
    
    args = parser.parse_args()
    
    # Загружаем данные
    print(f"Загружаем данные из {args.input_file}...")
    try:
        with open(args.input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Ошибка: Файл {args.input_file} не найден")
        return 1
    except json.JSONDecodeError as e:
        print(f"Ошибка: Некорректный JSON в файле {args.input_file}: {e}")
        return 1
    
    print(f"Загружено {len(data)} компаний")
    
    # Очищаем телефоны
    print("Начинаем очистку телефонов...")
    cleaned_data, removed_count, processed_companies = clean_phones_in_data(data)
    
    print(f"\nРезультаты:")
    print(f"- Обработано компаний: {processed_companies}")
    print(f"- Удалено некорректных номеров: {removed_count}")
    
    if not args.dry_run:
        # Сохраняем результат
        output_file = args.output or args.input_file
        print(f"Сохраняем очищенные данные в {output_file}...")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(cleaned_data, f, ensure_ascii=False, indent=4)
        
        print("Готово!")
    else:
        print("Режим dry-run: изменения не сохранены")
    
    return 0


if __name__ == '__main__':
    exit(main())