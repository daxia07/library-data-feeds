FROM python:3.8-slim-buster

# set up env
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONFAULTHANDLER 1

FROM base as python-deps

RUN pip install pipenv
RUN apt update && apt install -y --no-install-recommends gcc

RUN PIPENV_VENV_IN_PROJECT=1 pipenv install --deploy

FROM base as runtime

COPY --from=python-deps /.venv /.venv
ENV PATH="/app/.venv/bin:$PATH"

WORKDIR /app

COPY . .

EXPOSE 5000
CMD gunicorn main:app