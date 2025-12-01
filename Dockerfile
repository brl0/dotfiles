FROM ubuntu:latest

ENV DEBIAN_FRONTEND=noninteractive \
    NONINTERACTIVE=1 \
    CI=1 \
    LANG=en_US.UTF-8 \
    LANGUAGE=en_US:en \
    LC_ALL=en_US.UTF-8

SHELL ["/bin/bash", "-lc"]

# Create a non-root user (you can change the username if desired)
ARG USERNAME=ubuntu

# Create user if missing
RUN id -u "$USERNAME" >/dev/null 2>&1 || \
    useradd -m -s /bin/bash "$USERNAME" && \
    mkdir -p /home/"$USERNAME"

# Set the working directory to the user's home directory
WORKDIR /home/$USERNAME

COPY .files/scripts/install_from_conf.sh /tmp/install_from_conf.sh

# Install system packages
COPY .files/config/pkgs_sys.conf /tmp/pkgs_sys.conf
RUN /bin/bash /tmp/install_from_conf.sh /tmp/pkgs_sys.conf

# Set locale
RUN localedef -i en_US -f UTF-8 en_US.UTF-8

# Prepare brew directory
RUN mkdir -p /home/linuxbrew/.linuxbrew && chown -R $USERNAME:$USERNAME /home/linuxbrew

# Switch to the non-root user
USER $USERNAME

# Install brew packages
COPY .files/config/pkgs_brew.conf /tmp/pkgs_brew.conf
RUN /tmp/install_from_conf.sh /tmp/pkgs_brew.conf

ENV PATH="~/.local/bin:/home/linuxbrew/.linuxbrew/bin:~/.x-cmd.root/bin:${PATH}"

# Install user packages
COPY .files/config/pkgs_good.conf /tmp/pkgs_good.conf
RUN /tmp/install_from_conf.sh /tmp/pkgs_good.conf

# Install user packages
COPY .files/config/packages.conf /tmp/packages.conf
RUN /tmp/install_from_conf.sh /tmp/packages.conf

USER root
RUN rm -rf /tmp/*
USER $USERNAME

# Install dotfiles
# Recursively copy the local directory contents into the dotfiles folder
COPY . /home/$USERNAME/dotfiles/

# Set proper ownership of the copied files
USER root
RUN chown -R $USERNAME:$USERNAME /home/$USERNAME/dotfiles
USER $USERNAME

RUN chmod +x ~/dotfiles/.files/dotphiliac/install_dots.py \
    && mamba run python ~/dotfiles/.files/dotphiliac/install_dots.py

# Set the default command (can be overridden at runtime)
CMD ["/bin/bash", "-l"]
