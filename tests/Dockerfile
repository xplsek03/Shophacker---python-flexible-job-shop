FROM python:3.8.2
RUN python -m pip install numpy pymongo tornado bellmanford networkx matplotlib dnspython cryptography pathos
RUN python -m pip install -U pymoo

RUN mkdir shop
WORKDIR /shop
COPY . . 

EXPOSE 8888

CMD ["python", "server.py"]
