FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create a non-root user (optional)
# RUN adduser --disabled-password --geos '' botuser
# USER botuser

CMD ["python", "bot.py"]