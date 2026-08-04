# OS Provisioning and Build Instructions

This document contains the mechanical steps for setting up the operating system environment and building core components like llama.cpp.

## 1. Package Installation (Gentoo Linux)

```bash
# 必須パッケージ
emerge --ask sys-devel/gcc sys-devel/make dev-util/cmake dev-util/ninja dev-db/sqlite dev-lang/python:3.13 dev-libs/libxml2 dev-libs/libxslt dev-vcs/git
```

## 2. llama.cpp Build

```bash
git clone https://github.com/ggerganov/llama.cpp.git /opt/llm/llama.cpp
cd /opt/llm/llama.cpp
cmake -B build -DGGML_NATIVE=ON -DLLAMA_SERVER=ON -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release -j$(nproc)
```
