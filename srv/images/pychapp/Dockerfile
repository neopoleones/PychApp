FROM python

WORKDIR /app
COPY .. /app
RUN pip install -r /app/requirements.txt

EXPOSE 8080
EXPOSE 8081
CMD ["python3", "/app/pych.py"]