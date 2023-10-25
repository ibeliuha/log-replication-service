# Description
Asynchronous message replication web service
> Message format to publish is defined at `app/models/item.Item`

> For now secondaries depends on master and if master restart secondaries need to be restarted as well.\
> This problem is to be solved in next version 

### Supported features:
* configuration of response delay timer
* setting any number of secondary server replicas using only configuration parameters
* *write concern* - number of acnowledgments received by master from secondaries to acnowledge client of successful message delivery 
* *healthcheck* - master server ping its secondaries every *N* seconds in order to check their status
#### 2023-10-14
- backward synchronization (after new secondary registered master sends all his messages to it)
- logging
- retry mechanism
#### 2023-10-15
- adding in order messages from to secondaries message registry
#### 2023-10-25
- ***id*** of a secondary server is now set to `HOSTNAME` (shortened version of container id)
- global variables are moved to appropriate `__init__.py` files

### Service Operation Algorithm
1. After starting servers all secondaries send `POST /register` request to master in order for master to save them in its registry
2. Master makes asynchronous `GET /healthcheck` requests to secondaries every *N* seconds in order to keep track of their statuses. If secondary doesn't respond its status changes to `UNREACHABLE` and master doesn't replicate messages there until secondary changes its status to `HEALTHY` 
3. Master server endpoints for client:
   - `POST /messages/{wc:int}` - post new message to server
   - `GET /messages`  - get all messages on server
   - `GET /secondaries -H "x-token=[API_KEY]"` - list all registered secondaries
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
# wc parameter is optinal

curl -X PUT http://127.0.0.1:8000/messages?wc=1 \
-H "x-token: [API_KEY]" \
-H "Content-Type: application/json" \
-d '{"message":"hello world"}'
```
**Response**
```
{"message":"hello world","meta":{"message_id":1,"registered_at":"2023-10-14 15:27:10.277236","registered_to":["192.168.208.3:8000"]}}}
```
**Request**
```commandline
curl -X GET http://127.0.0.1:8000/messages \
-H "x-token: [API_KEY]"
```
**Response**
```
{"data": [{"message":"hello world","meta":{"message_id":1,"registered_at":"2023-10-14 15:27:10.277236","registered_to":["192.168.208.3:8000"]}}]}
```
**Request**
```commandline
curl -X GET http://127.0.0.1:8000/secondary/list \
-H "x-token: [API_KEY]"
```
**Response**
```
{"data": [{"host":"192.168.208.3","port":8000,"status":1,"last_healthy_status":"2023-10-14 15:32:02"}]}
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
* `SECONDARY_PORT` - exposed port for secondaries (only for Docker)
* `HEALTHCHECK_DELAY` - time period for checking status of secondaries
* `MAX_CONNECTION_TO_MASTER_DELAY` - number of seconds to wait until raise an error for secondary service to register to master
* `CONNECTION_TO_MASTER_RETRY_INTERVAL` - interval in seconds between secondary server registration retries 
* `CONNECTION_TO_MASTER_RETRY_MECHANISM`- await mechanism between retries. `exponential`| `uniform`
* `MAX_MESSAGE_POST_RETRY_DELAY` - number of seconds to wait until raise an error for publishing message to secondary
* `MESSAGE_POST_RETRY_INTERVAL` - interval in seconds between publishing retries
* `MESSAGE_POST_RETRIES_MECHANISM`- await mechanism between retries. `exponential`| `uniform`
> **NOTE:**
> If you set `exponential` to await mechanism, then interval will be increasing by the exponent of `5/4`

> Please define variable `SERVER_TYPE` in order to set server type as `master` or `secondary`.
 
> If you need custom delay for response on server, define `DELAY` in the form `lower,upper` **in seconds**.\
> Then for every publishing request to secondary random number of time to sleep would be chosen uniformly in given bounds\
> **FOR EXAMPLE**: When`DELAY=10,40` then server would be asleep for time between `10` and `40` seconds  

>It is possible to define lower`ge` and upper`le` bound for parameters in `app/services/config.Config` using `pydantic.Field`

# TO DO
   - [x] Add logic to assure that all messages added to all `HEALTHY` secondaries
   - [x] Set up logging
   - [x] Setup retries
   - [ ] Add tests
   - [ ] Add service diagram to README
   - [ ] Add service description to function handlers for more readable logging messages
   - [ ] Change server class definition in order to freely change server type in runtime
   - [ ] Add bidirectional ping between servers
   - [ ] Add persistent message store
    