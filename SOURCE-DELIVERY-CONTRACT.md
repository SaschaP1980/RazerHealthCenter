# Source Delivery Contract

Every new application version must be delivered with the complete, independently
buildable source snapshot in addition to the Portable ZIP.

Required artifacts per version:

1. Portable ZIP containing the runnable Windows application and runtime support
   directory structure.
2. Complete Source ZIP containing all Go source, Health Engine source, Repair
   Engine source, assets, PE resources, locale catalog, validators, build scripts
   and documentation required for an independent rebuild.

A standalone EXE is not a required user-facing artifact.
