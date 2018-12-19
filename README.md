# HP_MSA_Plugin
Plugin to retrieve metrics from the HP MSA API

https://support.hpe.com/hpsc/doc/public/display?docId=emr_na-a00017709en_us 

Example Usage:
./HPMSA.py --url http://{host}/api/show/snapshot-space --username {username} --password '{password}' --metric allocated-percent-snapspace --objects all --warning 90 --critical 95 --object_id pool

Example Response:
CRITICAL: A is above threshold: 95.0(99.5) | A_allocated-percent-snapspace=99.5 

Example Usage 2:
./HPMSA.py --url http://{host}/api/show/sensor-status --username {username} --password '{password}' --metric status --objects sensor_B.2,sensor_2.1.1 --warning "OK" --object_id durable-id

 No problems - OK  | sensor_B.2_status=OK sensor_2.1.1_status=OK 



