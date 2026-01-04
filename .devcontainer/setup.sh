#!/bin/bash
set -e

echo "Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y \
    build-essential \
    gcc \
    g++ \
    cmake \
    ninja-build \
    git \
    doxygen \
    graphviz \
    plantuml

echo "Upgrading pip..."
pip install --upgrade pip

echo "Installing Python package in development mode..."
cd python-lib
pip install -e ".[dev]"
cd ..

echo "Installing development tools"
pip install -r requirements.txt

echo "Installing documentation requirements..."
pip install -r docs/requirements.txt
