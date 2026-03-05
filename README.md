# Singapore Bus Tracker
A simple program that given the five-digit code for any bus stop in Singapore, fetches the next 3 arrivals.

## Usage
Give the five-digit code of the bus stop you want to get the arrival informarion for as a command argument and run the Python script.

## Notes on APIs and Tools Used
The API that I used for this program is the [official API](https://datamall.lta.gov.sg/content/dam/datamall/datasets/LTA_DataMall_API_User_Guide.pdf) provided by the Land Transport Authority by the Singaporean government. Specifically, I sued the Bus Arrival API on page 13 and the Bus Stops API on page 22 in the PDF.
I noticed that the Bus Stop API only fetches 500 bus stops per request, but since there are around 5,000 bus stops in Singapore, I refered to [this page](https://github.com/lta-rs/lta-rs/issues/18) and figured the API utilizes paigination to retrieve all the bus stops.

## Future Improvements
1. I think I'm doing too much work to get the first three arrivals for a bus stop, so I need to find a way to get them for all the bus lines that stop at the given bus stop.
2. Since bus stops rarely change, I might find a way to cache them locally by introducing a JSON file. 
3. I believe the error handling could be improved.
