# Description
Asynchronous replication web service

### Supported features:
* configuration of response delay timer
* setting any number of secondary server replicas using only configuration parameters
* *write concern* - number of acnowledgments received by master from secondaries to acnowledge client of successful message delivery 
* *healthcheck* - master server ping its secondaries every *N* seconds in order to check their status
#### 2023-10-14
- backward synchronization (after new secondary registered master sends all his messages to it)
- logging
- retry mechanism

### Service Operation Algorithm
1. After starting servers all secondaries send `POST /register` request to master in order for master to save them in its registry
2. Master makes asynchronous `GET /healthcheck` requests to secondaries every *N* seconds in order to keep track of their statuses. If secondary doesn't respond its status changes to `UNREACHABLE` and master doesn't replicate messages there until secondary changes its status to `HEALTHY` 
3. Master server endpoints for client:
   - `POST /messages/{wc:int}` - post new message to server\
   - `GET /messages`  - get all messages on server\
   - `GET /secondaries -H "x-token=[API_KEY]"` - list all registered secondaries\
   - `GET /healthcheck`

4. Secondary server endpoints for client:
   - `GET /messages -H "x-token=[API_KEY]` - get all messages on server
   - `GET /healthcheck`
5. For communication between services special token is used which is set in runtime by a program


# Usage
To start server execute a following:

```commandline
git clone git@github.com:ibeliuha/log-replication-service.git && cd log-replication-service
docker-compose up
docker-compose down
```
**Request**
```commandline
curl -X PUT http://127.0.0.1:8000/messages \
-H "x-token: [API_KEY]" \
-H "Content-Type: application/json" \
-d '{"message":"hello world"}'
   ```
**Response**
```
{"message":"hello world","meta":{"message_id":1,"registered_at":"2023-10-14 15:27:10.277236","registered_to":["192.168.208.3:8000"]}}%
```
**Request**
```commandline
curl -X GET http://127.0.0.1:8000/messages \
-H "x-token: [API_KEY]"
```
**Response**
```
{"1":{"message":"hello world","meta":{"message_id":1,"registered_at":"2023-10-14 15:27:10.277236","registered_to":["192.168.208.3:8000"]}}}%
```
**Request**
```commandline
curl -X GET http://127.0.0.1:8000/secondaries \
-H "x-token: [API_KEY]"
```
**Response**
```
{"192.168.208.3:8000":{"host":"192.168.208.3","port":8000,"status":1,"last_healthy_status":"2023-10-14 15:32:02"}}%
```
**Request**
```commandline
curl -X GET http://127.0.0.1:8000/healthcheck
```
**Response**
```
HEALTHY
```
# Configuration
In order to use service you should provide all necessary configs in **.env* file.
* `API_KEY` - define your own key in order to communicate with server
* `MASTER_HOST` - host of the master server which is used by secondaries to register. Using default as `http://master`
* `MASTER_PORT` - exposed port for master (if you deploy inside Docker then put exposed Docker's port for master)
* `SLAVE_PORT` - exposed port for secondaries (only for Docker)
* `HEALTHCHECK_DELAY` - time period for checking status of secondaries

> Please define variable `SERVER_TYPE` in order to set server type as `master` or `secondary`.
 
>If you need custom delay for response on server, define `DELAY` to any integer **in seconds**
 

# TO DO
   - [ ] Add logic to assure that all messages added to all `HEALTHY` secondaries
   - [x] Set up logging
   - [ ] Setup *smart* retries
   - [ ] Add service diagram to README
   - [ ] Change server class definition in order to freely change server type in runtime
   - [ ] Add service description to function handlers for more readable logging messages 
  

