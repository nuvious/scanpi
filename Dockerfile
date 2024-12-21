FROM python:latest
WORKDIR /
COPY . .
RUN pip3 install Flask
RUN apt update && apt install -y sane ocrmypdf
EXPOSE 5000
CMD ["python3", "./app.py"]
