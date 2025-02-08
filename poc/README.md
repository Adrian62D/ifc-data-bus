# start Docker
docker build -t nanomq .    
docker run -d --name nanomq -p 1883:1883 nanomq

# start python client
pip install paho-mqtt
python3 pub_sub_tcp.py
