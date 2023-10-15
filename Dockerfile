FROM python:3.11-alpine


WORKDIR app
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY app/. /app
ENTRYPOINT ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--log-config", "config/log_config.yaml"]
#ENTRYPOINT ["python", "-m", "main.py"]
#CMD ["pip", "install", "-r", "requirements.txt"]


#RUN pip install






