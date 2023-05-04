FROM python:3.8-slim

# Install pyspark and required packages
RUN pip3 install pyspark==3.3.0 \
    numpy pandas delta delta-spark \
    pyarrow h5py dataclasses shutils

# Install open jdk
RUN apt update -y
RUN apt install -y default-jre wget

# Setup required libraries for spark
RUN mkdir -p /opt/spark/jars

WORKDIR /tmp
RUN wget https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/1.12.389/aws-java-sdk-bundle-1.12.389.jar && \
    wget https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/3.3.4/hadoop-aws-3.3.4.jar && \
    wget https://repo1.maven.org/maven2/io/delta/delta-core_2.12/0.2.0/delta-core_2.12-0.2.0.jar && \
    wget https://repo1.maven.org/maven2/net/java/dev/jets3t/jets3t/0.9.4/jets3t-0.9.4.jar 

RUN mv *.jar /opt/spark/jars

# Setup jupyter lab for experimentation
RUN apt install -y gcc python3-dev
WORKDIR /app
CMD ["/bin/bash"]