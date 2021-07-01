# See here for image contents: https://github.com/microsoft/vscode-dev-containers/tree/v0.155.1/containers/python-3-miniconda/.devcontainer/base.Dockerfile

FROM mambaorg/micromamba:0.13.1

# RUN conda install mamba -n base -c conda-forge --yes

# Copy environment.yml (if found) to a temp locaition so we update the environment. Also
# copy "noop.txt" so the COPY instruction does not fail if no environment.yml exists.

# [Optional] Uncomment this section to install additional OS packages.
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends pkg-config make build-essential \
    iputils-ping git libgl1-mesa-glx

COPY environment.yml /root/environment.yml
# RUN micromamba env update -n base -f /root/environment.yml && rm /root/environment.yml
RUN micromamba install -y -n base -f /root/environment.yml && micromamba clean --all --yes
# [Optional] Uncomment to install a different version of Python than the default
# RUN conda install -y python=3.6 \
#     && pip install --no-cache-dir pipx \
#     && pipx reinstall-all

# RUN sed -i 's/${gitbranch}//'  /root/.bashrc