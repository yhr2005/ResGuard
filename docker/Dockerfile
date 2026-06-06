FROM ncbi/amr:latest

# 安装 wget 和 miniconda
RUN apt-get update && apt-get install -y wget && \
    wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O /tmp/miniconda.sh && \
    bash /tmp/miniconda.sh -b -p /opt/conda && \
    rm /tmp/miniconda.sh

# 接受 conda 默认频道的服务条款
RUN /opt/conda/bin/conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main && \
    /opt/conda/bin/conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r

# 安装 MOB-suite（添加 bioconda 频道）
RUN /opt/conda/bin/conda install -c bioconda mob_suite -y && \
    /opt/conda/bin/conda clean -a -y

# 将 conda 加入到 PATH
ENV PATH="/opt/conda/bin:${PATH}"