FROM postgres:13.3

COPY entrypoint.sh /usr/local/bin/

USER postgres

ENTRYPOINT ["entrypoint.sh"]

CMD ["postgres"]