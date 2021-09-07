import csv
import json
import logging
import os
import sys
import uuid as uuid_
from datetime import datetime, timezone

import click
from dictionaryutils import dump_schemas_from_dir
from gen3.tools import indexing
from indexclient import client

from g3po import __version__, helper, GEN3_URL

logger = logging.getLogger()
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter('%(message)s')  # print UNIX friendly format for PIPE use case
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

public_indexer = helper.build_public_indexer()


def check_healthy():
    if not public_indexer.is_healthy():
        click.echo(json.dumps({
            'GEN3_URL': GEN3_URL,
            'healthy': public_indexer.is_healthy()
        }))
        exit(1)
    return public_indexer.is_healthy()


@click.group()
def cli():
    pass


@cli.command()
def version():
    click.echo(json.dumps({
        'version': __version__
    }))


@cli.command()
@click.option('--count', default=1, help="Number of UUID to generate, default 1")
def uuid(count):
    uuid_list = []
    for c in range(count):
        uuid_list.append(str(uuid_.uuid4()))
    click.echo(json.dumps(uuid_list))


@cli.group()
def index():
    pass


@index.command()
def health():
    assert check_healthy()
    click.echo(json.dumps({
        'GEN3_URL': GEN3_URL,
        'healthy': public_indexer.is_healthy()
    }))


@index.command()
def stats():
    assert check_healthy()
    click.echo(json.dumps(public_indexer.get_stats()))


@index.command(name='list')
def index_list():
    assert check_healthy()
    click.echo(json.dumps(public_indexer.get_all_records()))


@index.command(name='get')
@click.argument('guid')
def index_get(guid):
    assert check_healthy()
    click.echo(json.dumps(public_indexer.get_record(guid=guid)))


@index.command(name='versions')
@click.argument('guid')
def index_versions(guid):
    assert check_healthy()
    click.echo(json.dumps(public_indexer.get_versions(guid=guid)))


@index.group()
def blank():
    pass


@blank.command(name='create')
@click.option('--uploader', help="Uploading user within system, e.g. user.name@g3po.org", required=True)
@click.option('--authz', help="Authz resources split by comma, e.g. /programs/program1/projects/P1", required=True)
@click.option('--filename', default=None, help="File name, e.g. test.bam")
@click.option('--cred', default=None, help="Path to credentials.json downloaded from your profile")
def blank_create(uploader, filename, authz, cred):
    indexer = helper.build_auth_indexer(cred)

    authz_list = str(authz).split(',')

    data = {
        'uploader': uploader,
        'file_name': filename,
        'authz': authz_list,
    }
    response = indexer.client._post(
        "index/blank",
        headers={"content-type": "application/json"},
        auth=indexer.client.auth,
        data=client.json_dumps(data),
    )
    response.raise_for_status()

    click.echo(json.dumps(response.json()))


@blank.command(name='update')
@click.option('--guid', help="Blank GUID/DID to update e.g. 1543974f-93e7-4f67-85ac-802e19ec11e8", required=True)
@click.option('--rev', help="Current revision e.g. 7bd043f3", required=True)
@click.option('--hash_type', help="Hash type e.g. md5", required=True)
@click.option('--hash_value', help="Hash value e.g. ab167e49d25b488939b1ede42752458b", required=True)
@click.option('--size', help="File size in bytes, e.g. 1024", type=int, required=True)
@click.option('--authz', help="Authz resources split by comma, e.g. /programs/program1/projects/P1", required=True)
@click.option('--urls', default=None,
              help="Resource URLs split by comma, e.g. s3://bucket/1543974f-93e7-4f67-85ac-802e19ec11e8/test.txt")
@click.option('--cred', default=None, help="Path to credentials.json downloaded from your profile")
def blank_update(guid, rev, hash_type, hash_value, size, urls, authz, cred):
    indexer = helper.build_auth_indexer(cred)

    authz_list = str(authz).split(',') if authz is not None else None
    url_list = str(urls).split(',') if urls is not None else None

    p = {'rev': rev}
    data = {
        'size': size,
        'hashes': {hash_type: hash_value},
        'urls': url_list,
        'authz': authz_list,
    }
    response = indexer.client._put(
        "index/blank/",
        guid,
        headers={"content-type": "application/json"},
        params=p,
        auth=indexer.client.auth,
        data=client.json_dumps(data),
    )
    response.raise_for_status()

    click.echo(json.dumps(response.json()))


@index.command(name='delete')
@click.argument('guid')
@click.option('--cred', default=None, help="Path to credentials.json downloaded from your profile")
def index_delete(guid, cred):
    indexer = helper.build_auth_indexer(cred)
    indexer.delete_record(guid=guid)


def _verify_manifest_format(tsv):
    return indexing.is_valid_manifest_format(
        manifest_path=tsv,
        column_names_to_enums=None,
        allowed_protocols=["s3", "gs", "https", "htsget", "gds", "file", "ftp", "gsiftp", "globus"],
        allow_base64_encoded_md5=False,
        error_on_empty_url=False,
        line_limit=None,
    )


@index.command()
def template():
    manifest_file = "manifest.tsv"
    if os.path.exists(manifest_file):
        click.echo(f"Found existing '{manifest_file}'. Abort for accidental override. Please rename it!")
        exit(0)

    click.echo(f"Generating 'manifest.tsv' ...")
    with open(manifest_file, "w") as tsv_file:
        writer = csv.writer(tsv_file, delimiter='\t')
        writer.writerow(["guid", "md5", "size", "file_name", "authz", "urls"])
        writer.writerow([str(uuid_.uuid4()), "d0df0d078def0a5d7eb8ed6eb1e06099", "7149868", "somatic-PASS.vcf.gz", "/programs/program1/projects/P1", "s3://g3po/SBJV001/2020-10-01/somatic-PASS.vcf.gz"])


@index.command()
@click.option('--tsv', default="manifest.tsv", help="Path to manifest.tsv file")
def validate(tsv):
    assert os.path.exists(tsv), f"{tsv} not found"

    if _verify_manifest_format(tsv):
        click.echo(f"{tsv} is valid!")


@index.command()
@click.option('--cred', default=None, help="Path to credentials.json downloaded from your profile")
@click.option('--tsv', default="manifest.tsv", help="Path to manifest.tsv file")
@click.option('--thread', default=8, help="Number of thread, default 8")
@click.option('--output', default=None, help="Output file")
def manifest(cred, tsv, thread, output):
    assert check_healthy()
    assert os.path.exists(tsv), f"{tsv} not found"

    utc_now_ts = int(datetime.utcnow().replace(tzinfo=timezone.utc).timestamp())
    if output is None:
        output = f"manifest_output_{utc_now_ts}.tsv"

    auth = helper.build_auth(cred)

    assert _verify_manifest_format(tsv) is True, f"Error in {tsv} format!"

    files, headers = indexing.index_object_manifest(
        commons_url=GEN3_URL,
        manifest_file=tsv,
        thread_num=thread,
        auth=auth,
        replace_urls=False,
        output_filename=output,
        manifest_file_delimiter="\t"  # put "," if the manifest is csv file
    )

    # logger.debug(json.dumps(files))


@cli.group()
def dd():
    pass


@dd.command()
@click.argument('schema')
@click.option('--out', default="schema.json", help="Output path")
def convert(schema, out):
    if os.path.isdir(out):
        out = os.path.join(out, "schema.json")
    click.echo(f"Writing schema into {out}...")
    with open(out, "w") as f:
        json.dump(dump_schemas_from_dir(schema), f)
