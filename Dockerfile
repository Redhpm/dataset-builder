FROM debian:stable-20230703-slim as downloader
# Downloads source codes from git, will later be used in the *-builder stages.
# We will always use fixed versions in order to have a consistent dataset (if it needs to be rebuilt).
# Builders do not depend on each other, this way, the build is parallelized.

RUN apt-get update && \
    apt-get install -y git

RUN git clone --depth 1 -b v2.41.0 https://github.com/git/git.git git

# Begining of builders stages.

FROM debian:stable-20230703-slim as git-builder

#git build dependencies.
RUN apt-get update && \
    apt-get install -y gcc make zlib1g-dev ssh gettext autoconf

# Copying source code and the list of flag to build with.
COPY --from=downloader git git
COPY flags.txt .

RUN mkdir /tmp/dbbuilder-output && cd git && \
    make configure && \
	while read flag || [ -n "$flag" ]; do \
    ./configure CFLAGS="-${flag}" && \
	make clean && NO_CURL=YesPlease NO_PERL=YesPlease NO_OPENSSL=YesPlease NO_EXPAT=YesPlease NO_TCLTK=YesPlease make && \
	mv git /tmp/dbbuilder-output/git_"$flag".bin ; \
    done < ../flags.txt
    
# End of builder stages.

FROM alpine:latest as final
# Using alpine image for temporary data storage. Version does not matter.
USER 65534:65534

# Creating directories.
WORKDIR /dataset
RUN mkdir git

COPY --from=git-builder /tmp/dbbuilder-output/* git