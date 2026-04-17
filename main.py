import asyncio
from datetime import datetime
import json
import os
import re
import sys
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
import httpx
import redis

load_dotenv()

async def fetch_arrival_info(station_id: str):
    url = f"https://datamall2.mytransport.sg/ltaodataservice/v3/BusArrival"
    api_key = os.getenv("API_KEY")
    headers = {"AccountKey": api_key}
    params = {"BusStopCode": station_id}
    async with httpx.AsyncClient() as client:
        r = await client.get(
            url, 
            headers=headers,
            params=params,
        )
    r.raise_for_status()
    data = r.json()
    services = data["Services"]
    first_3_arrivals = get_next_3_arrivals(services)
    await print_next_3_arrivals(station_id, first_3_arrivals)
    return services

def get_next_3_arrivals(services):
    first_3_arrivals = []
    for service in services:
        # If the first_3_arrivals list dosn't have any elements yet, initialize 
        # with the first three busses for the first service
        if not first_3_arrivals:
            first_3_arrivals.append((service["ServiceNo"], service["NextBus"]))
            first_3_arrivals.append((service["ServiceNo"], service["NextBus2"]))
            first_3_arrivals.append((service["ServiceNo"], service["NextBus3"]))
        else:
            next_3_busses = [service["NextBus"], service["NextBus2"], service["NextBus3"]]
            for bus in next_3_busses:
                # Skip if the estimated arrival time for the bus is empty.
                if not bus["EstimatedArrival"]:
                    break
                arrival_time = datetime.fromisoformat(bus["EstimatedArrival"])
                for index, arrival in enumerate(first_3_arrivals):
                    # Check if the item in first_3_arrivals is empty
                    if arrival[1]["EstimatedArrival"]:
                        first_arrival_time = datetime.fromisoformat(
                            arrival[1]["EstimatedArrival"]
                        )
                        if arrival_time < first_arrival_time:
                            first_3_arrivals.insert(
                                index,
                                (service["ServiceNo"], bus)
                            )
                            first_3_arrivals.pop()
                            break
                    else:
                        first_3_arrivals[index] = (service["ServiceNo"], bus)
                        break
        
    return first_3_arrivals

async def get_bus_stops():
    api_key = os.getenv("API_KEY")
    headers = {"AccountKey": api_key}

    # Retrieve cached bus stops
    bus_stops = get_cached_bus_stops()

    # Get bus stops that are not cached and cache them
    new_bus_stops = []
    skip = len(bus_stops)
    while True:
        async with httpx.AsyncClient() as client:
            url = f"https://datamall2.mytransport.sg/ltaodataservice/BusStops?$skip={skip}"
            r = await client.get(url, headers=headers)
            r.raise_for_status()
            data = r.json()
        if not data["value"]:
            break
        new_bus_stops.extend(data["value"])
        skip += 500
    cache_bus_stops(new_bus_stops)

    # Combine all the bus stops and return them
    bus_stops.extend(new_bus_stops)
    return bus_stops

def cache_bus_stops(bus_stops):
    r = redis.Redis(host="localhost", port=6379, decode_responses=True)
    for bus_stop in bus_stops:
        r.rpush("bus_stops", json.dumps(bus_stop))

def get_cached_bus_stops():
    r = redis.Redis(host="localhost", port=6379, decode_responses=True)

    # Convert raw string back to dictionaries
    raw_bus_stops = r.lrange("bus_stops", 0, -1)
    bus_stops = [json.loads(bus_stop) for bus_stop in raw_bus_stops]

    return bus_stops

async def print_next_3_arrivals(station_id, first_3_arrivals):
    bus_stops = await get_bus_stops()
    for bus_stop in bus_stops:
        if station_id == bus_stop["BusStopCode"]:
            current_time = datetime.now(ZoneInfo("Asia/Singapore"))
            timediff1 = datetime.fromisoformat(first_3_arrivals[0][1]["EstimatedArrival"]) - current_time
            timediff2 = datetime.fromisoformat(first_3_arrivals[1][1]["EstimatedArrival"]) - current_time
            timediff3 = datetime.fromisoformat(first_3_arrivals[2][1]["EstimatedArrival"]) - current_time
            est_arrival1 = current_time + timediff1
            est_arrival2 = current_time + timediff2
            est_arrival3 = current_time + timediff3
            print(f"Stop: {bus_stop['Description']}")
            print(f"1) {first_3_arrivals[0][0]} {int(timediff1.total_seconds() // 60)} min ({est_arrival1.strftime("%H:%M")})")
            print(f"2) {first_3_arrivals[1][0]} {int(timediff2.total_seconds() // 60)} min ({est_arrival2.strftime("%H:%M")})")
            print(f"3) {first_3_arrivals[2][0]} {int(timediff3.total_seconds() // 60)} min ({est_arrival3.strftime("%H:%M")})")

async def main():
    if len(sys.argv) < 2:
        print("Please add a bus stop code as an argument.")
        sys.exit()
    bus_stop_code = sys.argv[1]
    match = re.search(r'^\d{5}$', bus_stop_code)
    if match:
        print("Fetching arrival info...")
        await fetch_arrival_info(sys.argv[1])
    else:
        print("Bus Code not in the right format (5 digits)")

if __name__ == "__main__":
    asyncio.run(main())