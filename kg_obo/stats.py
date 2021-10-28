# stats.py

import csv
import os
import yaml # type: ignore
import boto3 # type: ignore

import kg_obo.upload

IGNORED_FILES = ["index.html","tracking.yaml","lock",
                "json_transform.log", "tsv_transform.log"]

def retrieve_tracking(bucket, track_file_remote_path, skip: list = [], 
                        get_only: list = [] ) -> list:
    """
    Downloads and parses the kg-obo tracking yaml.
    :param bucket: str of S3 bucket, to be specified as argument
    :param track_file_remote_path: path to the tracking file on the remote
    :return: dict of tracking file contents (OBO names, IRIs, and all versions)
    """   

    # We'll get a list of dicts so it's nicely iterable
    # Name isn't primary key as it may have multiple versions
    # So each OBO name + version is its own list entry
    versions = [] 

    track_file_local_path = "stats/tracking.yaml"

    client = boto3.client('s3')

    client.download_file(Bucket=bucket, Key=track_file_remote_path, Filename=track_file_local_path)

    with open(track_file_local_path, 'r') as track_file:
        tracking = yaml.load(track_file, Loader=yaml.BaseLoader)

    # Need to flatten a bit
    for name in tracking["ontologies"]:
        if name in skip:
            continue
        if len(get_only) > 0 and name not in get_only:
            continue
        current_version = tracking["ontologies"][name]["current_version"]
        versions.append({"Name": name, "Version": current_version})
        # See if there are archived versions
        if "archive" in tracking["ontologies"][name]:
            for entry in tracking["ontologies"][name]["archive"]:
                archive_version = entry["version"]
                versions.append({"Name": name, "Version": archive_version})
            
    return versions

def write_stats(stats) -> None:
    """
    Writes OBO graph stats to tsv.
    :param stats: dict of stats in which keys are OBO names
    """

    outpath = "stats/stats.tsv"
    columns = (stats[0]).keys()

    with open(outpath, 'w') as outfile:
        writer = csv.DictWriter(outfile, delimiter='\t',
                                fieldnames=columns)
        writer.writeheader()
        for entry in stats:
            writer.writerow(entry)
    
    print(f"Wrote to {outpath}")

def get_file_metadata(bucket, remote_path, versions) -> dict:
    """
    Given a list of dicts of OBO names and versions,
    retrieve their metadata from the remote.
    For now this only obtains the time each file was last modified.
    (This treats the JSON output identically to the TSV.)
    :param bucket: str of S3 bucket, to be specified as argument
    :param remote_path: str of remote directory to start from
    :param versions: list of dicts returned from retrieve_tracking
    :return: dict of dicts, with file paths as keys, versions and 2ary keys, 
                and metadata as key-value pairs
    """

    metadata = {}
    clean_metadata = {} # type: ignore

    client = boto3.client('s3')

    pager = client.get_paginator('list_objects_v2')

    names = []
    for entry in versions:
        names.append(entry["Name"])

    remote_files = [] # All file keys
    try:
        for page in pager.paginate(Bucket=bucket, Prefix=remote_path+"/"):
            remote_contents = page['Contents']
            for key in remote_contents:
                if os.path.basename(key['Key']) not in IGNORED_FILES and \
                    ((key['Key']).split("/"))[1] in names:
                    remote_files.append(key['Key'])
                    metadata[key['Key']] = {"LastModified": key['LastModified']}
        print(f"Found {len(remote_files)} matching objects in {remote_path}.")
    except KeyError:
        print(f"Found no existing contents at {remote_path}")

    # Clean up the keys so they're indexable
    for entry in metadata:
        name = (entry.split("/"))[1]
        version = (entry.split("/"))[2]
        if name in clean_metadata:
            clean_metadata[name][version] = metadata[entry]
        else:
            clean_metadata[name] = {version:metadata[entry]}

    return clean_metadata

def get_graph_details(bucket, remote_path, versions) -> dict:
    """
    Given a list of dicts of OBO names and versions,
    get details about their graph structure:
    node count, edge count, component count, and
    count of singletons.
    This is version-dependent.
    :param bucket: str of S3 bucket, to be specified as argument
    :param remote_path: str of remote directory to start from
    :param versions: list of dicts returned from retrieve_tracking
    :return: dict of dicts, with file paths as keys, versions and 2ary keys, 
                and metadata as key-value pairs
    """

    graph_details: Dict[Dict[Dict]] = {}

    return graph_details

def get_graph_stats(skip: list = [], get_only: list = [], bucket="bucket"):
    """
    Get graph statistics for all specified OBOs.
    :param skip: list of OBOs to skip, by ID
    :param get_only: list of OBOs to retrieve, by ID (otherwise do all)
    :param bucket: str of S3 bucket, to be specified as argument
    :return: boolean indicating success or existing run encountered (False for unresolved error)
    """
    success = True

    track_file_remote_path = "kg-obo/tracking.yaml"

    if len(skip) >0:
      print(f"Ignoring these OBOs: {skip}" )
    if len(get_only) >0:
       print(f"Will only retrieve these OBOs: {get_only}" ) 

    # Set up local directories
    if not os.path.exists("./stats/"):
        os.mkdir("stats")

    # Check for the tracking file first
    if not kg_obo.upload.check_tracking(bucket, track_file_remote_path):
        print("Cannot locate tracking file on remote storage. Exiting...")
        return False

    # Get current versions for all OBO graphs
    # Or just the specified ones
    versions = retrieve_tracking(bucket, track_file_remote_path, skip, get_only)

    # Get metadata from remote files
    metadata = get_file_metadata(bucket, "kg-obo", versions)

    # Get graph details
    # TODO: actually build this function
    graph_details = get_graph_details(bucket, "kg-obo", versions)

    # Now merge metadata into what we have from before
    for entry in versions:
        try:
            name = entry["Name"]
            version = entry["Version"]
            step = "metadata"
            entry.update(metadata[name][version])
            step = "graph details"
            entry.update(graph_details[name][version])
        except KeyError as e: #Some entries still won't have metadata
            print(f"Missing {step} for {name}, version {version}.")
            continue

    # Time to write
    write_stats(versions)

    return success
