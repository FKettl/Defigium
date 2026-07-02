FROM ubuntu:22.04 AS builder

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
	build-essential \
	cmake \
	git \
	libyaml-cpp-dev \
	libhiredis-dev \
	&& rm -rf /var/lib/apt/lists/*

WORKDIR /tmp
RUN git clone https://github.com/sewenew/redis-plus-plus.git && \
	cd redis-plus-plus && \
	mkdir build && cd build && \
	cmake -DREDIS_PLUS_PLUS_BUILD_TEST=OFF .. && \
	make && make install && \
	rm -rf /tmp/redis-plus-plus

WORKDIR /app

COPY . .

RUN make redis

FROM ubuntu:22.04 AS runtime

WORKDIR /app

RUN apt-get update && apt-get install -y \
	libyaml-cpp0.7 \
	libhiredis0.14 \
	&& rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/local/lib/libredis++.so* /usr/local/lib/
RUN ldconfig

COPY --from=builder /app/executor /app/executor

ENTRYPOINT ["./executor"]
