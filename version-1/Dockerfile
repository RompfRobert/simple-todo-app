FROM python:slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Copy requirements and install
COPY ../requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY version-1 /app

EXPOSE 5000

ENV FLASK_APP=app.py \
    FLASK_ENV=development

CMD ["python", "app.py"]