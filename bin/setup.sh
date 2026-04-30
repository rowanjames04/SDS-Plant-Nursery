#!/bin/bash
echo "=== Little Jill's Plant Nursery - Setup ==="
echo

if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python not found."
    echo "Please install Python from https://python.org/downloads"
    exit 1
fi

echo "[1/3] Installing dependencies..."
python3 -m pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "[ERROR] Dependency install failed."
    exit 1
fi

echo
echo "[2/3] Setting up database..."
python3 seed_db.py
if [ $? -ne 0 ]; then
    echo "[ERROR] Database seed failed."
    exit 1
fi

echo
echo "[3/3] Done!"
echo
echo "-----------------------------------------------"
echo "  Run the app:   ./bin/start.sh"
echo
echo "  Test accounts:"
echo "    Staff:    staff@littlejillsplantnursery.com  /  staff123"
echo "    Customer: customer@example.com               /  password123"
echo "-----------------------------------------------"
echo
