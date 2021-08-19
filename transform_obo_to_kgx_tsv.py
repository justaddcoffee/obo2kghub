import tempfile
from kgx.cli import transform
from tqdm import tqdm
import yaml
import requests
import urllib.request
import os

# this is a stable URL containing a YAML file that describes all the OBO ontologies:
# get the ID for each ontology, construct PURL
source_of_obo_truth = 'https://raw.githubusercontent.com/OBOFoundry/OBOFoundry.github.io/master/registry/ontologies.yml'

with urllib.request.urlopen(source_of_obo_truth) as f:
    yaml_content = f.read().decode('utf-8')
    yaml_parsed = yaml.safe_load(yaml_content)


def base_url_if_exists(oid):
    ourl = f"http://purl.obolibrary.org/obo/{oid}/{oid}-base.owl"
    try:
        ret = requests.head(ourl, allow_redirects=True)
        if ret.status_code != 200:
            ourl = f"http://purl.obolibrary.org/obo/{oid}.owl"
        else:
            i = 0
            for line in urllib.request.urlopen(ourl):
                i = i + 1
                if i > 3:
                    break
                l = line.decode('utf-8')
                if "ListBucketResult" in l:
                    ourl = f"http://purl.obolibrary.org/obo/{oid}.owl"

    except Exception:
        ourl = f"http://purl.obolibrary.org/obo/{oid}.owl"
    return ourl


for ontology in tqdm(yaml_parsed['ontologies'], "processing ontologies"):
    ontology_name = ontology['id']
    print(f"{ontology_name}")

    url = base_url_if_exists(ontology_name)  # take base ontology if it exists, otherwise just use non-base
    # TODO: generate base if it doesn't exist, using robot

    tf_input = tempfile.NamedTemporaryFile(prefix=ontology_name)
    tf_output_dir = tempfile.TemporaryDirectory()

    # download url
    urllib.request.urlretrieve(url, tf_input.name)

    # query kghub/[ontology]/current/*hash*

    # convert from owl to json using ROBOT

    # use kgx to convert OWL to KGX tsv
    transform(inputs=[tf_input.name],
              input_format='json',
              output=os.path.join(tf_output_dir.name, ontology_name),
              output_format='tsv',
              )

    # kghub/obo2kghub/bfo/2021_08_16|current/nodes|edges.tsv|date-hash
    os.system(f"ls -lhd {tf_output_dir.name}/*")
    # upload to S3
