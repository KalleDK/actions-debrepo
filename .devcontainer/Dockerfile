FROM mcr.microsoft.com/devcontainers/base:trixie

RUN apt update -q -y

RUN apt install -q -y python3 python3-typer python3-dotenv apt-utils gnupg direnv
RUN curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR="/usr/local/bin" sh
RUN curl -LsSf https://astral.sh/ruff/install.sh | env RUFF_INSTALL_DIR="/usr/local/bin" sh
RUN sh -c "$(curl --location https://taskfile.dev/install.sh)" -- -d -b /usr/local/bin
RUN UV_TOOL_DIR=/usr/local/share/uv/tools UV_TOOL_BIN_DIR=/usr/local/bin uv tool install -n bump-my-version
RUN UV_TOOL_DIR=/usr/local/share/uv/tools UV_TOOL_BIN_DIR=/usr/local/bin uv tool install -n pre-commit
RUN echo 'eval "$(direnv hook bash)"' >> /etc/bash.bashrc
