import base64
import datetime
import hashlib
import json
import os
import tempfile
from pathlib import Path

import requests
import streamlit as st


def push_file(
    content,
    repo_slug="TineGlaubitz/sonidb",
    user="TineGlaubitz",
    token=st.secrets["GH_TOKEN"],
):
    """
    Push file update to GitHub repo
    """
    name = hashlib.sha224(content).hexdigest()[:6]
    filename = f"data/{name}.json"
    branch = Path(filename).stem

    message = f"Automated upload created for the file {filename} as of {str(datetime.datetime.now())}"

    # create branch
    headers = {"Authorization": "Token " + token}
    url = f"https://api.github.com/repos/{repo_slug}/git/refs/heads"
    branches = requests.get(url, headers=headers).json()

    _branch, sha = branches[-1]["ref"], branches[-1]["object"]["sha"]
    res = requests.post(
        f"https://api.github.com/repos/{repo_slug}/git/refs",
        json={"ref": f"refs/heads/{branch}", "sha": sha},
        headers=headers,
    )

    # gathered all the data, now let's push
    inputdata = {}
    inputdata["branch"] = branch
    inputdata["message"] = message
    inputdata["content"] = base64.b64encode(content).decode("utf8")

    updateURL = f"https://api.github.com/repos/{repo_slug}/contents/{filename}"
    try:
        rPut = requests.put(updateURL, auth=(user, token), data=json.dumps(inputdata))
        if not rPut.ok:
            print("Error when pushing to %s" % updateURL)
            print("Reason: %s [%d]" % (rPut.text, rPut.status_code))
        print("Done!!\n")

    except requests.exceptions.RequestException as e:
        print(
            "Something went wrong! I will print all the information that is available so you can figure out what happend!"
        )
        print(rPut)
        print(rPut.headers)
        print(rPut.text)
        print(e)

    # Now create PR
    url = f"https://api.github.com/repos/{repo_slug}/pulls"

    payload = json.dumps(
        {
            "head": branch,
            "base": "main",
            "title": message,
            "body": "This is an automated PR.",
        }
    )
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    response = requests.request("POST", url, headers=headers, data=payload)


st.title("Submit to sonidb")

with st.form("submission_form"):

    name = st.text_input("name", help="Name of the sample, e.g. TiO2 rutile")
    particle_size = st.text_input(
        "particle size / nm",
        help="Feret diameter of the primary sample particle, measured with Transmission Electron Microscopy in nm",
    )
    composition = st.text_input(
        "composition", help="composition of the primary sample particle, e.g. ZnO"
    )
    energy_density = st.number_input(
        "energy density / J/mL",
        help="delivered sonication energy per sample volume, measured using calorimetry.",
    )
    z_av = st.number_input(
        "z average / nm",
        help="Obtained Z-average, measured using Dynamic Light Scattering.",
    )
    pdi = st.number_input(
        "PDI", help="Polydispersity Index, measured using Dynamic Light Scattering."
    )
    doi = st.text_input("DOI of reference")
    aff = st.text_input(
        "submitter name and affiliation",
        help="Please include your name and affiliation if you want it to appear in the database.",
    )
    comments = st.text_input(
        "comments", help="Any additional information you want to add"
    )

    # Every form must have a submit button.
    submitted = st.form_submit_button("Submit")
    if submitted:
        d = {
            "name": name,
            "particle_size": particle_size,
            "composition": composition,
            "energy_density": energy_density,
            "z_av": z_av,
            "pdi": pdi,
            "doi": doi,
            "name_affiliation": aff,
            "comments": comments,
        }
        push_file(json.dumps(d, ensure_ascii=False).encode("gbk"))
        st.write(f"Submitted {d}")
