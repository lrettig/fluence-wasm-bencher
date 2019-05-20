FROM ubuntu:18.04

# https://github.com/kuralabs/docker-python3-dev/blob/master/Dockerfile

# System deps
RUN apt-get update
RUN apt-get install -y software-properties-common git sudo build-essential wget curl nano \
    autoconf automake libtool make unzip zlib1g-dev texinfo \
    gcc musl-dev

# Install Python stack
RUN apt-get update \
    && apt-get --yes --no-install-recommends install \
        python3 python3-dev \
        python3-pip python3-venv python3-wheel python3-setuptools \
        build-essential \
        python-dev \
        graphviz git openssh-client \
    && rm -rf /var/lib/apt/lists/*


# install rust
RUN curl https://sh.rustup.rs -sSf | \
    sh -s -- --default-toolchain stable -y && . $HOME/.cargo/env
ENV PATH=/root/.cargo/bin:$PATH
RUN rustup default nightly-2019-01-15

RUN rustup target add wasm32-unknown-unknown


# Install Go 1.11
RUN add-apt-repository ppa:longsleep/golang-backports && apt-get update && apt-get install -y golang-go


# download geth
RUN go get -u -v github.com/ethereum/go-ethereum
RUN cd /root/go/src/github.com/ethereum/go-ethereum && git checkout v1.8.23
RUN ln -s /root/go/src/github.com/ethereum/go-ethereum /go-ethereum
#COPY ./sha1_test.go /go-ethereum/core/vm/runtime/sha_test.go
#RUN cd /go-ethereum/core/vm/runtime && go test -bench BenchmarkSHA1 -benchtime 5s

# Install cmake
RUN wget https://github.com/Kitware/CMake/releases/download/v3.14.3/cmake-3.14.3-Linux-x86_64.sh
RUN sh cmake-3.14.3-Linux-x86_64.sh --skip-license --prefix=/usr

# install evmone
RUN git clone --recursive https://github.com/chfast/evmone
RUN cd evmone && mkdir build
RUN cd evmone/build && cmake .. -DEVMONE_TESTING=ON
RUN cd evmone/build && cmake --build . -- -j
# /root/evmone/build/test/evmone-bench

# install python modules needed for benchmarking script
RUN pip3 install durationpy jinja2 pandas
# didnt alias python to python3 because it will break apt (assumes python is python2)


## build hera static libs
RUN apt-get install -y llvm-6.0-dev
RUN git clone --single-branch --branch benchmarking-static-lib https://github.com/cdetrio/hera
RUN cd hera && git submodule update --init
RUN cd hera && mkdir -p build
RUN cd hera/build && cmake -DBUILD_SHARED_LIBS=OFF -DHERA_BINARYEN=ON -DHERA_WABT=ON -DHERA_WAVM=ON -DHERA_DEBUGGING=OFF ..
RUN cd hera/build && cmake --build .
RUN cd hera/build/deps/src/binaryen-build/lib && for f in *.a; do ar x $f; done
RUN cd hera/build/deps/src/binaryen-build/lib && ar r -s -c libbinaryenfull.a *.o; rm *.o
RUN cd hera/build/deps/src/wavm-build/lib && for f in *.a; do ar x $f; done
RUN cd hera/build/deps/src/wavm-build/lib && ar r -s -c libwavm.a *.o; rm *.o
# /root/hera path is assumed by geth evmc6-static-lib branch
RUN ln -s /hera /root/hera

# install nodejs
RUN mkdir -p node
# RUN cd node && curl -fsSLO --compressed https://nodejs.org/dist/v11.10.0/node-v11.10.0-linux-x64.tar.gz
# need node 11.13.0 or 12 nightly for --experimental-wasm-bigint
RUN cd node && curl -fsSLO --compressed https://nodejs.org/download/nightly/v12.0.0-nightly20190325cdb87d9548/node-v12.0.0-nightly20190325cdb87d9548-linux-x64.tar.gz
RUN cd node && tar -xvf node-v12.0.0-nightly20190325cdb87d9548-linux-x64.tar.gz -C /usr/local/ --strip-components=1 --no-same-owner
RUN cd node && ln -s /usr/local/bin/node ./node
# /root/node is assumed by runherav8bench.py
RUN ln -s /node/node /root/node

RUN mkdir -p /evmraceresults
COPY ./evmrace /evmrace
COPY ./inputvectors /evmrace/inputvectors
COPY ./meterracer /meterracer
RUN chmod +x /meterracer/*.sh
WORKDIR /evmrace

CMD /bin/bash
