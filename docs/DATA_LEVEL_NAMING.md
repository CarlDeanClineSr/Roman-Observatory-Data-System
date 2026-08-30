# Roman Data-Level Naming

Never write a bare `L1` into a shared Roman/NVCPP record.

```text
SUN_EARTH_L1_SPACE_WEATHER  = physical location/domain used by space weather
WFI_LEVEL_1                 = Roman WFI processing level
CGI_LEVEL_1                 = Roman Coronagraph processing level
CGI_LEVEL_2A
CGI_LEVEL_2B
```

The namespaced labels preserve the distinction even when records are exported into the NVCPP astronomical domain.
