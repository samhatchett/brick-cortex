FROM ubuntu:xenial

RUN apt-get update

RUN apt-get install -y wget unzip python3.4 python3-pip
                       
WORKDIR /opt
RUN wget http://www.povray.org/ftp/pub/povray/Old-Versions/Official-3.62/Linux/povlinux-3.6.tgz
RUN tar -xvzf povlinux-3.6.tgz && cd povray-3.6 && ./install -no-arch-check && mv povray /bin/

WORKDIR /bin
RUN wget http://www.hassings.dk/l3/l3p/l3p14betalinux.zip && unzip l3p14betalinux.zip && rm l3p14betalinux.zip

WORKDIR /opt
RUN wget http://www.ldraw.org/library/updates/complete.zip && unzip complete.zip && rm complete.zip
ENV LDRAWDIR=/opt/ldraw
# library now in /opt/ldraw

RUN pip3 install numpy

WORKDIR /app
COPY render.py render.py
COPY lights.pov lights.pov
COPY inventory.db inventory.db
COPY povray.conf /usr/local/etc/povray/3.6/povray.conf

WORKDIR /data
RUN mkdir /data/img
VOLUME /data

CMD python3 /app/render.py


