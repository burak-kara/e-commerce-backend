FROM python:3.8
ENV PYTHONUNBUFFERED=1
WORKDIR /code
COPY requirements.txt /code/
RUN pip install -r requirements.txt
COPY . /code/
EXPOSE 8000
RUN chmod 777 /code/src/manage.py
CMD ["python","src/manage.py","makemigrations"]
CMD ["python","src/manage.py","migrate"]
CMD ["python","src/manage.py","runsslserver","0.0.0.0:8000"]