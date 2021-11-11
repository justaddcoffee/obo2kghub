import urllib
import requests  # type: ignore


def get_url(oid):
    ourl = f"http://purl.obolibrary.org/obo/{oid}/{oid}.owl"
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
