FROM python
COPY ./app /app
WORKDIR /app
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r /app/requirements.txt
RUN rm /app/requirements.txt
RUN rm /app/config.yml
RUN mv /app/config.prod.yml /app/config.yml
CMD ["python", "app.py"]