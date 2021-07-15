# See here for image contents: https://github.com/microsoft/vscode-dev-containers/tree/v0.155.1/containers/python-3-miniconda/.devcontainer/base.Dockerfile

FROM condaforge/mambaforge

# RUN conda install mamba -n base -c conda-forge --yes

# Copy environment.yml (if found) to a temp locaition so we update the environment. Also
# copy "noop.txt" so the COPY instruction does not fail if no environment.yml exists.

# [Optional] Uncomment this section to install additional OS packages.
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends pkg-config make build-essential \
    iputils-ping git libgl1-mesa-glx libgl1-mesa-dev libxi6 libnvidia-egl-wayland-dev \
    mesa-utils libxft-dev libglew-dev libglfw3-dev \
    && apt clean \
    && rm -rf /var/lib/apt/lists/*

ADD environment.yml /root/
RUN mamba env update -n base -f /root/environment.yml && mamba clean --all --yes

# Install jive and its dependencies
RUN mamba install -c beenje jive
RUN mamba install xorg-libxtst

# Create XDG_RUNTIME_DIR
RUN mkdir -p /tmp/runtime-root && chmod -R 700 /tmp/runtime-root

# [Optional] Uncomment to install a different version of Python than the default
# RUN conda install -y python=3.6 \
#     && pip install --no-cache-dir pipx \
#     && pipx reinstall-all

# RUN sed -i 's/${gitbranch}//'  /root/.bashrc