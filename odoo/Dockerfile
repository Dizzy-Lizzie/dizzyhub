FROM  odoo:14 AS release

USER root

COPY parse_db_url.sh /usr/local/lib
COPY odoo_cmds /usr/local/bin/
COPY ./entrypoint.sh /
COPY requirements.txt ./

#allocate odoo user a login shell
RUN chsh -s /bin/bash odoo

FROM release AS local

ARG USERNAME=odoo
ARG USER_UID=1000
ARG USER_GID=$USER_UID
ARG WORKSPACE_DIR=/workspace/odoo

RUN \
    # prevent vscode from being reinstalled on every run
    mkdir -p /home/$USERNAME/.vscode-server/extensions \
        /home/$USERNAME/.vscode-server-insiders/extensions; \
    chown -R $USERNAME:$USERNAME \
        /home/$USERNAME/.vscode-server \
        /home/$USERNAME/.vscode-server-insiders; \
    # preserve command line history
    SNIPPET="export PROMPT_COMMAND='history -a' && export HISTFILE=/commandhistory/.bash_history"; \
    mkdir /commandhistory; \
    touch /commandhistory/.bash_history; \
    chown -R $USERNAME:$USERNAME /commandhistory; \
    echo $SNIPPET >> "/home/$USERNAME/.bashrc"; \
    # update user id of all files owned by odoo
    odoo_uid=`id -u odoo`; \
    usermod -u $USER_UID odoo; \
    groupmod -g $USER_GID odoo; \
    find /etc -user $odoo_uid -exec chown odoo:odoo {} \;;

RUN python3 -m pip install \
    debugpy \
    # better xml validation errors for odoo
    jingtrang \
    pytest-odoo

RUN apt-get update && export DEBIAN_FRONTEND=noninteractive; \
    apt-get -y install --no-install-recommends \
        # needed for jingtrang python module
        default-jre

RUN echo "root:pass" | chpasswd

#ENV ODOO_RC=$WORKSPACE_DIR/odoo.local.conf
ENV ODOO_ADDONS_PATH=$WORKSPACE_DIR
ENV ENV=local

USER odoo

CMD ["bash"]



FROM release

ENV ENV=production
ENV ODOO_ADDONS_PATH=/addons

RUN mkdir /addons; \
    chown odoo:odoo /addons; \
    python3 -m pip install -r requirements.txt;

USER odoo

COPY eb_garment /addons/eb_garment
COPY lizzie_main /addons/lizzie_main




