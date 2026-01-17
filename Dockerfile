FROM python:3.11-slim
WORKDIR /app

# Cài các package cơ bản ổn định
COPY requirements-base.txt .
RUN pip install --no-cache-dir -r requirements-base.txt

# Cài các package thay đổi thường xuyên
COPY requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements-dev.txt