# docker build -t firmadyne .
FROM ubuntu:14.04

# Update packages
RUN apt-get update && apt-get upgrade -y && apt-get install -y sudo

# Create firmadyne user
RUN useradd -m firmadyne
RUN echo "firmadyne:firmadyne" | chpasswd && adduser firmadyne sudo

# Run setup script
ADD setup.sh /tmp/setup.sh
RUN /tmp/setup.sh
ADD startup.sh /firmadyne/startup.sh

USER firmadyne
ENTRYPOINT ["/firmadyne/startup.sh"]
CMD ["/bin/bash"]
