FROM python:3.8-slim-buster

# set up env
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONFAULTHANDLER 1

#FROM base as python-deps
WORKDIR /app
RUN mkdir /app/.venv

RUN pip install pipenv

#FROM base as runtime

#COPY --from=python-deps /.venv /.venv
ENV PATH="/app/.venv/bin:$PATH"
RUN apt update && apt install -y --no-install-recommends gcc

COPY . .
RUN PIPENV_VENV_IN_PROJECT=1 pipenv install --deploy

EXPOSE 5000
CMD gunicorn -b 0.0.0.0:$PORT wsgi:app