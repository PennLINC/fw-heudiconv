import logging

def foo():
    return None


# FOR EACH ASL SCAN
# 1. read in the json file
# 2. read in the metadata extras
# 3. merge the two above

# 4. get the dimensions of the asl scan
# 5. create a dataframe that alternates label-control or control-label up to number of volumes
# 6. write this dataframe to ASLContext.tsv

# FOR EACH DELTA SCAN
# 1. add metadata to sidecar
# 2. get dimensions of scan
# 3. create a dataframe that writes 'CBF' for each volume
# 4. write this dataframe to ASLContext.tsv for that scan

# Create a list with all of the ASL+DELTA+sidecars' paths

# FOR EACH MZERO SCAN
# 1. add metadata to sidecar
# 2. create an IntendedFor in m0 sidecar
# 3. Loop through other files
# 4. check if the shim in this MZERO matches the shim in the file
# 5. Add this file to IntendedFor
# 6. create a dataframe that writes 'MZeroScan' for each volume in M0
# 7. write this dataframe to ASLContext.tsv for that scan

# Do the same above for fieldmaps folder
