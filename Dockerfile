FROM python:latest
RUN pip3 install Flask
RUN apt update && apt install -y sane ocrmypdf
WORKDIR /
COPY . .
EXPOSE 5000
CMD ["python3", "./app.py"]
