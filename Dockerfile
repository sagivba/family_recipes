FROM ruby:3.3.4-slim

ENV LANG=C.UTF-8 \
    BUNDLE_PATH=/bundle \
    BUNDLE_BIN=/bundle/bin \
    GEM_HOME=/bundle \
    PATH=/bundle/bin:$PATH

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    pkg-config \
    libffi-dev \
    zlib1g-dev \
    libgmp-dev \
    libssl-dev \
    libxml2-dev \
    libxslt1-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /site

RUN gem update --system && gem install bundler

COPY Gemfile Gemfile.lock* /site/
RUN bundle install || true

CMD ["bash"]
