FROM debian:trixie-slim

RUN apt update -q -y

RUN apt install -q -y python3 python3-typer python3-dotenv apt-utils gnupg

COPY tools/make-deb/create-markdown.py /usr/local/bin/create-markdown
RUN chmod +x /usr/local/bin/create-markdown

COPY tools/make-deb/sign-repo.py /usr/local/bin/sign-repo
RUN chmod +x /usr/local/bin/sign-repo

COPY tools/create-gpg.sh /usr/local/bin/create-gpg
RUN chmod +x /usr/local/bin/create-gpg

COPY tools/create-repo.sh /usr/local/bin/create-repo
RUN chmod +x /usr/local/bin/create-repo

RUN mkdir -p /etc/repoconf
COPY conf/apt-ftparchive.conf conf/stable.conf conf/testing.conf /etc/repoconf/

WORKDIR /root


CMD ["/usr/local/bin/create-repo"]
