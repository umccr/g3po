FROM python:3.6-slim
COPY . /g3po
WORKDIR /g3po
RUN pip install --no-cache-dir .
CMD [ "g3po", "--help" ]
# ENTRYPOINT ["/usr/local/bin/g3po"]
