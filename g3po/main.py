import json
import logging
import os
from datetime import datetime, timezone

import click
from gen3.auth import Gen3Auth
from gen3.index import Gen3Index
from gen3.tools.indexing import index_object_manifest
from indexclient import client

from g3po import __version__

GEN3_URL = os.getenv("GEN3_URL", "https://gen3.dev.umccr.org/")
gen3_index = Gen3Index(GEN3_URL)

logger = logging.getLogger(__name__)


def check_healthy():
    if not gen3_index.is_healthy():
        click.echo(json.dumps({
            'GEN3_URL': GEN3_URL,
            'healthy': gen3_index.is_healthy()
        }))
        exit(1)
    return gen3_index.is_healthy()


def _jwt_indexer(cred):
    assert check_healthy()
    assert os.path.exists(cred), f"{cred} not found"
    auth = Gen3Auth(GEN3_URL, refresh_file=cred)
    return Gen3Index(GEN3_URL, auth_provider=auth)


@click.group()
def cli():
    pass


@cli.command()
def version():
    click.echo(json.dumps({
        'version': __version__
    }))


@cli.group()
def index():
    pass


@index.command()
def health():
    assert check_healthy()
    click.echo(json.dumps({
        'GEN3_URL': GEN3_URL,
        'healthy': gen3_index.is_healthy()
    }))


@index.command()
def stats():
    assert check_healthy()
    click.echo(json.dumps(gen3_index.get_stats()))


@index.command(name='list')
def index_list():
    assert check_healthy()
    click.echo(json.dumps(gen3_index.get_all_records()))


@index.command(name='get')
@click.argument('guid')
def index_get(guid):
    assert check_healthy()
    click.echo(json.dumps(gen3_index.get_record(guid=guid)))


@index.command(name='versions')
@click.argument('guid')
def index_versions(guid):
    assert check_healthy()
    click.echo(json.dumps(gen3_index.get_versions(guid=guid)))


@index.group()
def blank():
    pass


@blank.command(name='create')
@click.option('--uploader', help="Uploading user within system, e.g. user.name@g3po.org", required=True)
@click.option('--authz', help="Authz resources split by comma, e.g. /programs/program1/projects/P1", required=True)
@click.option('--filename', default=None, help="File name, e.g. test.bam")
@click.option('--cred', default="credentials.json", help="Path to credentials.json i.e. API key from your profile")
def blank_create(uploader, filename, authz, cred):
    indexer = _jwt_indexer(cred)

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
@click.option('--cred', default="credentials.json", help="Path to credentials.json i.e. API key from your profile")
def blank_update(guid, rev, hash_type, hash_value, size, urls, authz, cred):
    indexer = _jwt_indexer(cred)

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
@click.option('--cred', default="credentials.json", help="Path to credentials.json i.e. API key from your profile")
def index_delete(guid, cred):
    indexer = _jwt_indexer(cred)
    indexer.delete_record(guid=guid)


@index.command()
@click.option('--cred', default="credentials.json", help="Path to credentials.json i.e. API key from your profile")
@click.option('--tsv', default="manifest.tsv", help="Path to manifest.tsv file, refer README")
@click.option('--thread', default=8, help="Number of thread, default 8")
@click.option('--output', default=None, help="Output file")
def manifest(cred, tsv, thread, output):
    assert check_healthy()
    assert os.path.exists(cred), f"{cred} not found"
    assert os.path.exists(tsv), f"{tsv} not found"

    utc_now_ts = int(datetime.utcnow().replace(tzinfo=timezone.utc).timestamp())
    if output is None:
        output = f"manifest_output_{utc_now_ts}.tsv"

    auth = Gen3Auth(GEN3_URL, refresh_file=cred)

    files, headers = index_object_manifest(
        commons_url=GEN3_URL,
        manifest_file=tsv,
        thread_num=thread,
        auth=auth,
        replace_urls=False,
        output_filename=output,
        manifest_file_delimiter="\t"  # put "," if the manifest is csv file
    )

    # logger.debug(json.dumps(files))
