# Use Ubuntu as the base image
FROM ubuntu:latest

ENV DEBIAN_FRONTEND=noninteractive

# Create a non-root user (you can change the username if desired)
ARG USERNAME=ubuntu

# Set the working directory to the user's home directory
WORKDIR /home/$USERNAME

RUN apt-get update && \
    apt-get install -y apt-utils build-essential curl file git ruby-full locales sudo

RUN localedef -i en_US -f UTF-8 en_US.UTF-8

COPY .files/scripts/install_from_conf.sh /tmp/install_from_conf.sh
COPY .files/config/pkgs_sys.conf /tmp/pkgs_sys.conf

# Install system packages
RUN /bin/bash /tmp/install_from_conf.sh /tmp/pkgs_sys.conf && \
    apt-get clean && rm -rf /var/lib/apt/lists/* /var/tmp/* && \
    chown -R $USERNAME:$USERNAME /home/linuxbrew && \
    echo "Done installing system packages."

# USER root
ENV PATH="~/.local/bin:/home/linuxbrew/.linuxbrew/bin:~/.x-cmd.root/bin:${PATH}"

# Switch to the non-root user
USER $USERNAME

COPY .files/config/packages.conf /tmp/packages.conf

# Install user packages
RUN /bin/bash /tmp/install_from_conf.sh /tmp/packages.conf

USER root
RUN rm -rf /tmp/*
# RUN useradd -m -s /bin/bash $USERNAME
USER $USERNAME

# Set the default command (can be overridden at runtime)
CMD ["bash"]

# Recursively copy the local directory contents into the dotfiles folder
COPY . /home/$USERNAME/dotfiles/

# Set proper ownership of the copied files
USER root
RUN chown -R $USERNAME:$USERNAME /home/$USERNAME/dotfiles
USER $USERNAME

RUN ~/dotfiles/.files/dotphiliac/install_dots.py
