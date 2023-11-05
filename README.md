# solar-tracker (WIP)

Playing with solar panels that track the sun's movement for better efficiency.

<div style="display:flex;">
    <img src="images/1000001418.jpg" alt="Alt text" width="400" height="400" style="margin-right:10px;">
    <img src="images/1000001418.jpg" alt="Alt text" width="400" height="400">
</div>

## Starting up

```bash
# Create volume persistant grafana config
docker volume create solar-tracker-grafana

# Start grafana
docker run --rm -d -p 3000:3000 --name=grafana --volume grafana-storage:/var/lib/grafana grafana/grafana:10.2.0

# Create volume persistant grafana config
docker volume create solar-tracker-influxdb

# Start influxdb
docker run --rm -d -p 8086:8086 --name=influxdb --volume solar-tracker-influxdb:/var/lib/influxdb2 influxdb:2.7.3

# Start mosquitto
docker run -d --rm --name mosquitto -p 1883:1883 -p 9001:9001 -v ${PWD}/config/mosquitto.conf:/mosquitto/config/mosquitto.conf eclipse-mosquitto:2.0.18

```