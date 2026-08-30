# Data Boundaries

Roman is an astronomical-observatory system. It is not part of LUFT and it is not a Sun-Earth L1 space-weather feed.

## Hard firewall

```text
Roman public pages / MAST metadata / simulations / ground tests
                            |
                            v
             Roman Observatory Data System
                            |
              explicit small hashed export
                            v
          NVCPP ASTRONOMICAL_OBSERVATORY only
```

The following paths are closed:

```text
Roman -> SUN_EARTH_L1_SPACE_WEATHER   FORBIDDEN
Roman -> PLASMA_PIPELINE               FORBIDDEN
Roman -> chi_B24M                      FORBIDDEN
Roman -> GANNON_HOLDOUT                FORBIDDEN
```

A simulation, workshop product, detector ground test, page change, or archive row cannot be relabeled as flight data without explicit provenance.
