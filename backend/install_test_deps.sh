#!/bin/bash

echo "Установка зависимостей для тестирования..."
echo ""

SERVICES=("users" "meters" "announcements" "chat" "notifications")

for service in "${SERVICES[@]}"; do
    echo "Устанавливаем зависимости для $service..."
    cd "$service" || exit 1

    if [ ! -d "venv" ]; then
        echo "  Создаем виртуальное окружение..."
        python3 -m venv venv
    fi

    source venv/bin/activate

    if [ -f "requirements.txt" ]; then
        echo "  Устанавливаем основные зависимости..."
        pip install -r requirements.txt -q
    fi

    if [ -f "requirements-test.txt" ]; then
        echo "  Устанавливаем тестовые зависимости..."
        pip install -r requirements-test.txt -q
    else
        echo "$service: нет файла requirements-test.txt"
    fi

    deactivate
    echo "$service: установлено"

    cd ..
done

echo ""
echo "Готово! Теперь можно запускать тесты:"
echo ""
echo "  ./run_all_tests.sh        # Все тесты"
echo "  cd users && source venv/bin/activate && pytest -v     # Только users"
echo ""
