import sys
import json
import time
import requests

try:
    # SETUP / DEFAULT RESOURCES
    host = "https://cms.lingotek.com"
    access_token = "b068b8d9-c35b-3139-9fe2-e22ee7998d9f"  # sandbox token
    community_id = "f49c4fca-ff93-4f01-a03e-aa36ddb1f2b8"  # sandbox community
    project_id = "103956f4-17cf-4d79-9d15-5f7b7a88dee2"  # sandbox project

    # prepare common headers for each request
    headers = {
        "Authorization": "Bearer {0}".format(access_token)
    }

    # COMMUNITY
    print "\nCOMMUNITY"
    res = requests.get("{0}/api/community".format(host), headers=headers)
    print "\t{0}".format(res.status_code)
    print "\t{0}".format(res.text)

    # PROJECT
    print "\nPROJECT"
    res = requests.get("{0}/api/project/{1}".format(host, project_id), headers=headers)
    if res.status_code == 200:
        res_json = res.json()
        print "\tProject (existing): {0} ({1})".format(res_json['properties']['title'], res_json['properties']['id'])
    else:
        project_title = "Sample Project"
        payload = {
            "title": project_title,
            "workflow_id": "c675bd20-0688-11e2-892e-0800200c9a66", # machine translation workflow
            "community_id": community_id
        }
        res = requests.post("{0}/api/project".format(host), data=payload, headers=headers)
        if res.status_code == 201:
            res_json = res.json()
            project_id = res_json['properties']['id']
            print "\tProject created: {0} ({1})".format(project_title, project_id)
        else:
            print "\t {0}".format(res.status_code)
            print "\tThere was an error creating the project."
            sys.exit(0)

    # CREATE DOCUMENT
    print "\nDOCUMENT"
    
    source_locale_code = "en-US"
    document_title = "Test Title {0}".format(int(round(time.time() * 1000)))
    payload = {
        "title": document_title,
        "project_id": project_id,
        "format": "JSON",
        "charset": "UTF-8",
        "locale_code": source_locale_code,
    }

    # NOTE: use one of the following methods to set the content parameter ...
    
    # to use a String to specify content
    # create some sample content as JSON
    content = {
        "title": "Test Title", 
        "body": "The quick brown fox jumped over the lazy dog."
    }
    payload["content"] = json.dumps(content)
    
    # to use a File to specify content
    #payload["content"] = open("/path/to/file", "rb")

    res = requests.post("{0}/api/document".format(host), files=payload, headers=headers)
    if res.status_code == 202:
        res_json = res.json()
        document_id = res_json['properties']['id']
        print "\t{0} ({1})".format(source_locale_code, res.status_code)
        print "\t{0}".format(document_id)
    else:
        print "\t {0}".format(res.status_code)
        print "\tFailed to upload the document."
        sys.exit(0)

    # CHECK IMPORT PROGRESS
    print "\nIMPORT STATUS"
    imported = False
    for i in range(30):
        time.sleep(3)
        status_message = "\t {0} | check status:".format(i)
        res = requests.get("{0}/api/document/{1}".format(host, document_id), headers=headers)
        if res.status_code == 404:
            status_message += " => importing"
        else:
            status_message += " => imported!"
            imported = True
        status_message += " ({0})".format(res.status_code)
        print status_message
        
        if imported:
            break
        elif(i == 30 and not imported):
            print "\tDocument never completed imported."
            sys.exit(0)

    # REQUEST TRANSLATION
    print "\nREQUEST TRANSLATION"
    translation_locale_code = "zh-CN"
    payload = {
        "locale_code": translation_locale_code
    }
    res = requests.post("{0}/api/document/{1}/translation".format(host, document_id), data=payload, headers=headers)
    print "\t{0} => {1} ({2})".format(document_id, translation_locale_code, res.status_code)

    # CHECK OVERALL PROGRESS
    print "\tTRANSLATION STATUS"
    for i in range(50):
        time.sleep(3)
        status_message = "\t {0} | progress:".format(i)
        res = requests.get("{0}/api/document/{1}/status".format(host, document_id), headers=headers)
        res_json = res.json()
        progress = res_json['properties']['progress']
        status_message += " {0}%".format(progress)
        status_message += " ({0})".format(res.status_code)
        print status_message
    
        if progress == 100:
            break
        elif i == 50:
            print "\tDocument never completed imported."
            sys.exit(0)

    # DOWNLOAD TRANSLATIONS
    print "\nDOWNLOAD TRANSLATIONS"
    download_headers = {
        "Accept": "application/json, text/plain, */*"
    }
    payload = {
        "locale_code": translation_locale_code
    }
    res = requests.get("{0}/api/document/{1}/content".format(host, document_id), params=payload, headers=dict(headers, **download_headers))
    print "\t{0} ({1})".format(translation_locale_code, res.status_code)
    print "\t", res.text
    
    # DELETE DOCUMENT
    print "\nCLEANUP"
    res = requests.delete("{0}/api/document/{1}".format(host, document_id), headers=headers)
    print "\tDelete Document: {0} ({1})".format(document_id, res.status_code)
    if res.status_code != 204:
        print "\tFailed to delete document."
        print res.text
        sys.exit(0)

except Exception, err:
    print Exception, err
