FROM python:3.12-slim

# Ishchi katalog
WORKDIR /app

# Muhit o'zgaruvchilari
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Kerakli paketlarni o'rnatish
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Loyiha kodini ko'chirish
COPY . /app/

# Port
EXPOSE 8000

# Ishga tushirish buyrug'i
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
