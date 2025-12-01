FROM python:3.11-slim

WORKDIR /app

ARG DEEPSEEK_API_KEY
ENV DEEPSEEK_API_KEY=$DEEPSEEK_API_KEY

COPY . /app
RUN pip install --no-cache-dir -r requirements.txt
CMD ["python", "app.py"]
EXPOSE 5000
EXPOSE 8000