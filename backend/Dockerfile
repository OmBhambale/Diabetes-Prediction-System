FROM python:3.12

WORKDIR /app

COPY requirements*.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 4000

CMD ["waitress-serve" ,"--listen=*:4000" ,"app:app"]